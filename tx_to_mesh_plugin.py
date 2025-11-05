#!/usr/bin/env python3
"""
TX to Mesh Plugin for MMRelay

This plugin filters Matrix messages to Meshtastic, allowing only messages
that start with the !tx command to be relayed to the mesh network.

Author: mate71pl
License: MIT
"""

from typing import Any, Dict, Optional

# Import the base plugin class
try:
    from base_plugin import BasePlugin
except ImportError:
    # Fallback for different import structures
    try:
        from plugins.base_plugin import BasePlugin
    except ImportError:
        from mmrelay.plugins.base_plugin import BasePlugin


class Plugin(BasePlugin):
    """
    TX to Mesh Plugin

    This plugin intercepts Matrix messages before they are sent to Meshtastic
    and only allows messages that start with '!tx' to be relayed.
    When a message starts with '!tx', the command prefix is stripped before
    sending to the mesh network.
    """

    plugin_name = "tx_to_mesh"

    def __init__(self):
        """Initialize the plugin with configuration."""
        super().__init__()

        # Plugin configuration is loaded by BasePlugin from the global config
        # and available as self.config
        self.plugin_config = self.config

        # Configuration options with defaults
        self.command_prefix = self.plugin_config.get("command_prefix", "!tx")
        self.strip_prefix = self.plugin_config.get("strip_prefix", True)
        self.case_sensitive = self.plugin_config.get("case_sensitive", False)
        self.allow_empty_message = self.plugin_config.get("allow_empty_message", False)

        # Log plugin initialization
        self.logger.info("TX to Mesh Plugin initialized")
        self.logger.info(f"Command prefix: '{self.command_prefix}'")
        self.logger.info(f"Strip prefix: {self.strip_prefix}")
        self.logger.info(f"Case sensitive: {self.case_sensitive}")
        self.logger.info(
            f"Allow empty message after prefix: {self.allow_empty_message}"
        )

    async def handle_room_message(self, _room, event, full_message) -> bool:
        """
        Handle Matrix messages and claim them for forwarding to Meshtastic.

        This method intercepts Matrix room messages and filters them based on
        the command prefix. Only messages starting with the configured prefix
        are relayed to the mesh network.

        Args:
            room: Matrix room object
            event: Matrix event object
            full_message: The full message content/dict

        Returns:
            bool: True if message was claimed and handled, False otherwise
        """
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
            if not content and not self.allow_empty_message:
                self.logger.warning("tx_to_mesh: empty after prefix; blocking")
                return True  # Claimed, do not fall through

            # Optionally keep or strip prefix
            to_send = content if self.strip_prefix else msg

            # Send to mesh via BasePlugin helper (queued & rate-limited)
            try:
                await self.send_message(to_send)
                self.logger.info("tx_to_mesh: relayed to mesh")
            except Exception:
                self.logger.exception("tx_to_mesh: failed to relay")
            return True  # Claimed
        return False

    async def handle_meshtastic_message(
        self, packet, formatted_message: str, longname: str, meshnet_name: str
    ):
        """
        Handle Meshtastic messages (pass-through, no filtering needed).

        This plugin only filters Matrix -> Meshtastic messages, so Meshtastic
        messages are passed through unchanged.

        Args:
            packet: Meshtastic packet
            formatted_message: The formatted message content
            longname: Long name of the Meshtastic node
            meshnet_name: Name of the source mesh network
        """
        # This plugin doesn't need to process Meshtastic messages
        # All Meshtastic -> Matrix messages pass through unchanged
        pass

    def get_matrix_commands(self) -> Dict[str, str]:
        """
        Return available Matrix commands for this plugin.

        Returns:
            Dict[str, str]: Dictionary of commands and their descriptions
        """
        return {
            self.command_prefix: f"Send message to Meshtastic network (prefix: {self.command_prefix})"
        }

    def get_plugin_info(self) -> Dict[str, Any]:
        """
        Return plugin information and status.

        Returns:
            Dict[str, Any]: Plugin information
        """
        return {
            "name": self.plugin_name,
            "version": "1.0.0",
            "description": "Filters Matrix messages to Meshtastic using !tx command prefix",
            "author": "mate71pl",
            "status": "active",
            "config": {
                "command_prefix": self.command_prefix,
                "strip_prefix": self.strip_prefix,
                "case_sensitive": self.case_sensitive,
                "allow_empty_message": self.allow_empty_message,
            },
        }

    async def handle_plugin_command(
        self, command: str, _args: list, _room_id: str, _sender_id: str
    ) -> Optional[str]:
        """
        Handle plugin-specific commands from Matrix.

        Args:
            command: The command name
            args: List of command arguments
            room_id: Matrix room ID
            sender_id: Matrix user ID of the sender

        Returns:
            Optional[str]: Response message, or None
        """
        if command == "tx_filter_status":
            info = self.get_plugin_info()
            return (
                f"TX to Mesh Plugin Status:\n"
                f"• Command prefix: {info['config']['command_prefix']}\n"
                f"• Strip prefix: {info['config']['strip_prefix']}\n"
                f"• Case sensitive: {info['config']['case_sensitive']}\n"
                f"• Allow empty message: {info['config']['allow_empty_message']}\n"
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
        "command_prefix": {
            "type": "string",
            "default": "!tx",
            "description": "Command prefix to filter messages (default: !tx)",
        },
        "strip_prefix": {
            "type": "boolean",
            "default": True,
            "description": "Remove command prefix from message before sending to Meshtastic",
        },
        "case_sensitive": {
            "type": "boolean",
            "default": False,
            "description": "Make command prefix matching case sensitive",
        },
        "allow_empty_message": {
            "type": "boolean",
            "default": False,
            "description": "Allow sending messages that are empty after removing prefix",
        },
    },
}
