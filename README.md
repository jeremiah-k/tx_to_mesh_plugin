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
    command_prefix: "!tx"
    strip_prefix: true
    case_sensitive: false
    allow_empty_message: false
    priority: 10
```

## Configuration

| Option                | Type    | Default | Description                                         |
| --------------------- | ------- | ------- | --------------------------------------------------- |
| `command_prefix`      | string  | `"!tx"` | Command prefix to filter messages                   |
| `strip_prefix`        | boolean | `true`  | Remove command prefix before sending to mesh        |
| `case_sensitive`      | boolean | `false` | Make prefix matching case sensitive                 |
| `allow_empty_message` | boolean | `false` | Allow empty messages after removing prefix          |
| `priority`            | integer | `10`    | Plugin execution priority (lower = higher priority) |

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
2. Plugin checks if message starts with configured prefix
3. If matched, claims the message (returns `True`) to prevent other plugins from processing it
4. Optionally strips the prefix based on configuration
5. Forwards the message to Meshtastic using the rate-limited `send_message()` helper
6. Logs success/failure for debugging

## Development

This plugin follows MMRelay's BasePlugin interface:

- **`handle_room_message()`**: Processes Matrix messages and returns boolean to claim them
- **`handle_meshtastic_message()`**: Pass-through for mesh messages (no filtering needed)
- **`get_matrix_commands()`**: Returns list of commands for help system
- **`description` property**: Provides help text for the plugin
- **`get_config_schema()`**: Defines configuration validation schema

## License

MIT License - see LICENSE file for details.
