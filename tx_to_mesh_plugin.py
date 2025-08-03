#!/usr/bin/env python3
"""
TX to Mesh Plugin for MMRelay

This plugin filters Matrix messages to Meshtastic, allowing only messages
that start with the !tx command to be relayed to the mesh network.

Author: mate71pl
License: MIT
"""

import asyncio
import logging
from typing import Optional, Dict, Any

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

    def __init__(self, config: Dict[str, Any]):
        """Initialize the plugin with configuration."""
        super().__init__(config)

        # Plugin configuration - get from the plugins section
        self.plugin_config = config.get("plugins", {}).get(self.plugin_name, {})

        # Configuration options with defaults
        self.command_prefix = self.plugin_config.get("command_prefix", "!tx")
        self.strip_prefix = self.plugin_config.get("strip_prefix", True)
        self.case_sensitive = self.plugin_config.get("case_sensitive", False)
        self.allow_empty_message = self.plugin_config.get("allow_empty_message", False)

        # Log plugin initialization
        self.logger.info(f"TX to Mesh Plugin initialized")
        self.logger.info(f"Command prefix: '{self.command_prefix}'")
        self.logger.info(f"Strip prefix: {self.strip_prefix}")
        self.logger.info(f"Case sensitive: {self.case_sensitive}")
        self.logger.info(f"Allow empty message after prefix: {self.allow_empty_message}")

    async def handle_matrix_message(self, room, event, formatted_message: str,
                                   sender_id: str, meshnet_name: str) -> Optional[str]:
        """
        Handle Matrix messages before they are sent to Meshtastic.

        This method intercepts Matrix room messages and filters them based on
        the !tx command prefix. Only messages starting with !tx are allowed
        to be relayed to the mesh network.

        Args:
            room: Matrix room object
            event: Matrix event object
            formatted_message: The formatted message content
            sender_id: Matrix user ID of the sender
            meshnet_name: Name of the target mesh network

        Returns:
            Optional[str]: Modified message to send to Meshtastic, or None to block
        """

        # Get the original message content
        original_message = formatted_message.strip()

        if not original_message:
            self.logger.debug("Empty message received, skipping")
            return None

        # Check command prefix (case sensitivity handling)
        command_prefix = self.command_prefix
        check_message = original_message

        if not self.case_sensitive:
            command_prefix = command_prefix.lower()
            check_message = original_message.lower()

        # Check if message starts with the command prefix
        if not check_message.startswith(command_prefix):
            self.logger.debug(f"Message does not start with '{self.command_prefix}', blocking relay")
            return None

        # Log that we're processing a valid command
        self.logger.info(f"Processing !tx command from {sender_id} in {meshnet_name}")

        # Extract the message content after the command prefix
        if self.strip_prefix:
            # Remove the command prefix and any following whitespace
            message_content = original_message[len(self.command_prefix):].lstrip()

            # Check if we allow empty messages after stripping prefix
            if not message_content and not self.allow_empty_message:
                self.logger.warning(f"Empty message after removing '{self.command_prefix}' prefix, blocking relay")
                return None

            self.logger.debug(f"Stripped prefix, sending: '{message_content}'")
            return message_content
        else:
            # Keep the full message including prefix
            self.logger.debug(f"Keeping full message: '{original_message}'")
            return original_message

    async def handle_meshtastic_message(self, packet, formatted_message: str,
                                      longname: str, meshnet_name: str):
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
                "allow_empty_message": self.allow_empty_message
            }
        }

    async def handle_plugin_command(self, command: str, args: list,
                                  room_id: str, sender_id: str) -> Optional[str]:
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
            return f"TX to Mesh Plugin Status:\n" \
                   f"• Command prefix: {info['config']['command_prefix']}\n" \
                   f"• Strip prefix: {info['config']['strip_prefix']}\n" \
                   f"• Case sensitive: {info['config']['case_sensitive']}\n" \
                   f"• Status: {info['status']}"

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
            "description": "Command prefix to filter messages (default: !tx)"
        },
        "strip_prefix": {
            "type": "boolean",
            "default": True,
            "description": "Remove command prefix from message before sending to Meshtastic"
        },
        "case_sensitive": {
            "type": "boolean",
            "default": False,
            "description": "Make command prefix matching case sensitive"
        },
        "allow_empty_message": {
            "type": "boolean",
            "default": False,
            "description": "Allow sending messages that are empty after removing prefix"
        }
    }
}

