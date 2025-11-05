#!/usr/bin/env python3
"""
TX to Mesh Plugin for MMRelay

This plugin filters Matrix messages to Meshtastic, allowing only messages
that start with the !tx command to be relayed to the mesh network.

Author: mate71pl
License: MIT
"""

from typing import Any, Dict, Optional

# Import the base plugin class and config
from mmrelay.plugins.base_plugin import BasePlugin, config

# Import message formatting functions
from mmrelay.matrix_utils import get_meshtastic_prefix
from mmrelay.constants.formats import DEFAULT_MESHTASTIC_PREFIX


class Plugin(BasePlugin):
    """
    TX to Mesh Plugin

    This plugin intercepts Matrix messages before they are sent to Meshtastic
    and only allows messages that start with '!tx' to be relayed.
    When a message starts with '!tx', the command prefix is stripped before
    sending to the mesh network.

    Required Configuration:
        channels: List of Meshtastic channels to monitor (REQUIRED)
            Example: channels: [0, 1, 3]
            This plugin requires explicit channel configuration for safety.

    Optional Configuration:
        command_prefix: Command prefix to filter messages (default: "!tx")
        case_sensitive: Make prefix matching case sensitive (default: False)

    Example Configuration:
        plugins:
            tx_to_mesh:
                active: true
                channels: [0, 1, 3]  # REQUIRED
                command_prefix: "!tx"
    """

    plugin_name = "tx_to_mesh"

    def __init__(self):
        """
        Initialize the TX-to-Mesh plugin and load runtime options.

        Loads plugin configuration from self.config (provided by BasePlugin) and initializes these runtime options with their defaults: `command_prefix` (default: "!tx"), `strip_prefix` (default: True), and `case_sensitive` (default: False). Records initialization details to the plugin logger.
        """
        super().__init__()

        # Configuration options with defaults
        self.command_prefix = self.config.get("command_prefix", "!tx")
        self.case_sensitive = self.config.get("case_sensitive", False)

        # Log plugin initialization
        self.logger.debug("TX to Mesh Plugin initialized")
        self.logger.debug(f"Command prefix: '{self.command_prefix}'")
        self.logger.debug(f"Case sensitive: {self.case_sensitive}")

    async def handle_room_message(self, room, event, full_message) -> bool:
        """
        Claim Matrix room messages that start with the configured command prefix and relay them to the mapped Meshtastic channel.

        If the Matrix room maps to a configured channel and the message begins with `command_prefix` (respecting `case_sensitive`), the plugin will send either the content after the prefix or the full message to that channel depending on `strip_prefix`. An empty message after prefix removal is considered handled (claimed) but not forwarded. Room and message data may be taken from the `room`, `event`, or `full_message` objects.

        Parameters:
            room: Matrix room object (used to obtain `room_id` when available).
            event: Matrix event object (used to obtain message `body` when available).
            full_message: Dict-like message payload that may contain `room_id` and `body`.

        Returns:
            bool: `true` if the message was claimed/handled and should not be processed further, `false` otherwise.
        """
        # This plugin only handles Matrix -> Meshtastic messages, not DMs
        # Always return False for DMs to ignore direct commands
        # Matrix messages should be mapped to specific Meshtastic channels

        # Find the channel for this room using matrix_rooms config
        room_id = getattr(room, "room_id", None) or full_message.get("room_id")
        if not room_id:
            return False

        # Look up channel in matrix_rooms config
        matrix_rooms = config.get("matrix_rooms", [])
        channel = None
        for room_config in matrix_rooms:
            if room_config["id"] == room_id:
                channel = room_config["meshtastic_channel"]
                break

        if channel is None:
            self.logger.debug(
                f"tx_to_mesh: room {room_id} not found in matrix_rooms config"
            )
            return False

        if not self.is_channel_enabled(channel, is_direct_message=False):
            self.logger.debug(
                f"tx_to_mesh: channel {channel} not enabled for room {room_id}"
            )
            return False

        # Extract message body from event or full_message
        body = getattr(event, "body", None) or full_message.get("body") or ""
        if not isinstance(body, str):
            return False

        msg = body.strip()
        if not msg:
            return False

        # Match command prefix
        prefix = self.command_prefix
        candidate = msg[: len(prefix)]

        if (
            (candidate == prefix)
            if self.case_sensitive
            else (candidate.lower() == prefix.lower())
        ):
            content = msg[len(prefix) :].lstrip()
            if not content:
                # Ignore empty messages after prefix removal
                self.logger.debug("tx_to_mesh: empty after prefix; ignoring")
                return True  # Claimed, do not fall through

            # Get sender display name for proper attribution
            display_name = (
                room.user_name(event.sender) if hasattr(room, "user_name") else None
            )
            if not display_name:
                # Fallback to extracting localpart from sender's Matrix ID
                sender_id = event.sender
                display_name = (
                    sender_id.split(":")[0][1:] if ":" in sender_id else sender_id
                )

            # Generate proper sender prefix using configured matrix prefix format
            sender_prefix = get_meshtastic_prefix(config, display_name, event.sender)

            # Construct message with sender attribution (never include !tx prefix)
            to_send = f"{sender_prefix}{content}"

            # Send to mesh via BasePlugin helper (queued & rate-limited)
            try:
                self.send_message(to_send, channel=channel)
                self.logger.info(f"tx_to_mesh: relayed to mesh on channel {channel}")
            except Exception as e:
                self.logger.error(
                    f"tx_to_mesh: failed to relay on channel {channel}: {e}",
                    exc_info=True,
                )
            return True  # Claimed
        else:
            # Message doesn't have prefix, but we claim it to prevent fallback relay
            self.logger.debug(
                f"tx_to_mesh: blocked message without prefix on channel {channel}"
            )
            return True  # Claimed but not relayed

    async def handle_meshtastic_message(
        self, _packet, formatted_message: str, longname: str, meshnet_name: str
    ):
        """
        Pass-through handler for incoming Meshtastic messages.

        This plugin does not process Meshtastic-origin messages and declines them so other plugins can handle them.

        Parameters:
            packet: Meshtastic packet object.
            formatted_message (str): The formatted message content.
            longname (str): Long name of the Meshtastic node that sent the message.
            meshnet_name (str): Name of the source mesh network.

        Returns:
            `False` to indicate the message was not handled and should be passed to other plugins.
        """
        # This plugin only filters Matrix -> Meshtastic, not the reverse
        # Always return False to let other plugins handle Meshtastic messages
        return False

    def get_matrix_commands(self) -> Dict[str, str]:
        """
        Return a mapping of the configured Matrix command prefix to its user-facing description.

        Returns:
            Dict[str, str]: A dict where the key is the plugin's `command_prefix` and the value is the command description shown to users.
        """
        return {
            self.command_prefix: f"Send message to Meshtastic network (prefix: {self.command_prefix})"
        }

    def get_plugin_info(self) -> Dict[str, Any]:
        """
        Provide plugin metadata and current configuration values.

        Returns:
            Dict[str, Any]: Dictionary with plugin metadata: `name`, `version`, `description`, `author`, `status`, and a `config` mapping containing `command_prefix`, `strip_prefix`, and `case_sensitive`.
        """
        return {
            "name": self.plugin_name,
            "version": "1.0.0",
            "description": "Filters Matrix messages to Meshtastic using !tx command prefix",
            "author": "mate71pl",
            "status": "active",
            "config": {
                "command_prefix": self.command_prefix,
                "case_sensitive": self.case_sensitive,
            },
        }

    async def handle_plugin_command(
        self, command: str, _args: list, _room_id: str, _sender_id: str
    ) -> Optional[str]:
        """
        Produce a response for the "tx_filter_status" plugin command.

        Parameters:
            command (str): The plugin command to handle.

        Returns:
            Optional[str]: A formatted status string when `command` is "tx_filter_status", `None` otherwise.
        """
        if command == "tx_filter_status":
            info = self.get_plugin_info()
            return (
                f"TX to Mesh Plugin Status:\n"
                f"• Command prefix: {info['config']['command_prefix']}\n"
                f"• Case sensitive: {info['config']['case_sensitive']}\n"
                f"• Status: {info['status']}"
            )

        return None


# Plugin metadata for MMRelay
PLUGIN_INFO = {
    "name": "tx_to_mesh",
    "version": "1.0.0",
    "description": "Filters Matrix messages to Meshtastic using !tx command prefix",
    "author": "mate71pl",
    "requires": [],
    "config_schema": {
        "channels": {
            "type": "list",
            "required": True,
            "description": "List of Meshtastic channels to monitor for Matrix messages (required)",
        },
        "command_prefix": {
            "type": "string",
            "default": "!tx",
            "description": "Command prefix to filter messages (default: !tx)",
        },
        "case_sensitive": {
            "type": "boolean",
            "default": False,
            "description": "Make command prefix matching case sensitive",
        },
    },
}
