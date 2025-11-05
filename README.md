# TX to Mesh Plugin for MMRelay

A plugin for MMRelay that filters Matrix messages and only forwards messages starting with a specific command prefix (default: `!tx`) to the Meshtastic network.

## Features

- **Command Filtering**: Only messages starting with `!tx` (or configured prefix) are relayed to Meshtastic
- **Prefix Stripping**: Optionally removes the command prefix before sending to mesh
- **Case Sensitivity**: Configurable case-sensitive prefix matching
- **Empty Message Handling**: Configurable behavior for empty messages after prefix removal
- **Priority Control**: Runs early to claim messages before other plugins

## Installation

Add this plugin as a community plugin in your MMRelay `config.yaml`:

```yaml
community-plugins:
  tx_to_mesh:
    active: true
    repository: https://github.com/mate71pl/tx_to_mesh_plugin.git
    tag: main # or specify a version tag like v1.0.0
    channels: [0, 1, 2, 3, 4]  # Required: Specify which channels to monitor
    command_prefix: "!tx"
    strip_prefix: true
    case_sensitive: false
    allow_empty_message: false
    priority: 10
```

**Important**: You must specify the `channels` parameter. This plugin requires explicit channel configuration to function properly.

## Configuration

| Option                | Type    | Default | Description                                         |
| --------------------- | ------- | ------- | --------------------------------------------------- |
| `channels`            | list    | **Required** | List of Meshtastic channels to monitor for Matrix messages |
| `command_prefix`      | string  | `"!tx"` | Command prefix to filter messages                   |
| `strip_prefix`        | boolean | `true`  | Remove command prefix before sending to mesh        |
| `case_sensitive`      | boolean | `false` | Make prefix matching case sensitive                 |
| `allow_empty_message` | boolean | `false` | Allow empty messages after removing prefix          |
| `priority`            | integer | `10`    | Plugin execution priority (lower = higher priority) |

### Channel Configuration

**Required**: You must specify the `channels` parameter in your configuration. This plugin will only process Matrix messages that are destined for the configured Meshtastic channels.

**Channel Examples**:
```yaml
# Monitor all channels (recommended for most use cases)
channels: [0, 1, 2, 3, 4]

# Monitor only specific channels
channels: [0, 2]  # Only primary and longfast channels

# Monitor no channels (DMs only)
channels: []  # Only respond to direct messages
```

The channel numbers correspond to your Meshtastic channel configuration in `matrix_rooms`.

## Usage

### Basic Usage

Send messages to Meshtastic by prefixing with `!tx`:

```text
!tx Hello mesh network!
```

If `strip_prefix` is `true` (default), only "Hello mesh network!" will be sent to the mesh.
If `strip_prefix` is `false`, the full "!tx Hello mesh network!" will be sent.

### Help Integration

The plugin integrates with MMRelay's help system:

- `!help` - Lists all available commands including `!tx`
- `!help tx` - Shows description for the tx command

## How It Works

1. Matrix messages are intercepted by `handle_room_message()`
2. Plugin checks if the message is for a configured channel using `is_channel_enabled()`
3. Plugin checks if the message starts with the configured prefix
4. If matched, claims the message (returns `True`) to prevent other plugins from processing it
5. Optionally strips the prefix based on configuration
6. Forwards the message to Meshtastic using the rate-limited `send_message()` helper
7. Logs success/failure for debugging

### Channel Handling

- **Matrix Messages**: Always considered "direct messages" for channel checking since they come from Matrix rooms
- **Meshtastic Messages**: Checked against actual channel numbers and direct message status
- **Channel Filtering**: Only processes messages destined for configured channels in `channels` list

## Development

This plugin follows MMRelay's BasePlugin interface:

- **`handle_room_message()`**: Processes Matrix messages and returns boolean to claim them
- **`handle_meshtastic_message()`**: Pass-through for mesh messages (no filtering needed)
- **`get_matrix_commands()`**: Returns list of commands for help system
- **`description` property**: Provides help text for the plugin
- **`get_config_schema()`**: Defines configuration validation schema

## License

MIT License - see LICENSE file for details.
