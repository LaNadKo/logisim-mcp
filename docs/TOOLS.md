# MCP tool catalog

54 tools. See [tools.json](../tools.json) for exact argument schemas.

| Tool | Description |
|---|---|
| projects | List live projects with unambiguous session refs |
| project_new | Create a new live project using the current template |
| project_open | Open a workspace .circ project without replacing existing projects |
| project_close | Close a live project window. Refuses unsaved changes unless discard_changes=true; refuses the last project to avoid exiting the runtime. |
| native_roots | Get typed refs to project, circuit, simulator, appearance, options and canvas |
| catalog_full | Every loaded component and editor tool, all native default attributes and handles |
| circuit_snapshot | Read components, exact ports, net values, wires and width conflicts |
| component_inspect | Inspect one component by stable session ref or Factory@x,y id |
| circuit_edit | One undoable batch: add component; wire points; remove_wire exact from/to; remove; attribute key/value; move/duplicate x/y. Validate whole batch before applying. Move does not reroute wires. |
| pins_read_write | Read all pins, or set input values (unsigned integer or exact-width 01xE string). Supports 1..32 bits; propagates and repaints. |
| net_probe | Read simulated value at a wire/port coordinate |
| circuit_manage | List/add/select/remove/reorder/set-main circuit or set circuit attribute. Removal refuses used/last circuit. |
| project_save | Save workspace .circ. Existing destination requires overwrite=true and is backed up first. |
| analyzer_create | Create native combinational analyzer, up to 8 one-bit inputs and outputs |
| analyzer_capture | Derive truth table and expressions from current combinational circuit; unsuitable for sequential circuits |
| analyzer_set_expression | Parse native Boolean syntax for one output (AND, OR, XOR, NOT or symbolic equivalents) |
| analyzer_set_table | Set complete output truth-table columns, row order binary ascending; accepts 0,1,x |
| analyzer_minimize | Native SOP/POS minimization with optional application to output expressions. Use when requested or required by the assignment; do not infer permission for a compact implementation. Follow logisim://guidance/agents. |
| analyzer_read | Read analyzer expressions, minimized forms and full truth table |
| analyzer_build | Native automatic circuit generation into a new circuit; optional two-input and NAND-only gates. Preserve the requested full structure and basis; no unrequested compact alternative. Check generated structure against the assignment. Follow logisim://guidance/agents. NAND-only cannot directly synthesize XOR expressions. |
| memory_read_write | Read/write RAM state or ROM contents, 0-based addresses, unsigned words. Runtime RAM values are not stored in .circ; use export. ROM writes change project. |
| circuit_export | Export native circuit drawing to PNG/GIF/JPEG; state colors, printer view and scale options |
| project_options | Read all native simulation options or set one native attribute |
| library_manage | Load .circ or JAR library from workspace, reload loaded library, or unload unused library. JAR class_name is required for extension libraries. |
| simulation_substate | Enter live subcircuit instance state or return to parent simulation state |
| menu_inventory | Enumerate complete actual native application menu tree, enabled state and item handles |
| menu_action | Queue a previously discovered native menu action. Can open modal UI, print, save or close; observe completion separately. Does not imply external submission approval. |
| log_create | Create native signal logging model for the current simulation state |
| log_select | Add components to native logger; RAM accepts address option. Discover supported logging types in manual. |
| log_sample | Sample native selected log signals after propagation |
| log_file | Configure native logger output file/header/enabled; new workspace path only. Uses the active application logging model for continuous transitions. |
| api_describe | Discover constructors, methods and fields for a native com.cburch class or handle, including package-private APIs. Filter methods by substring. Discovery does not prove behavioral coverage. |
| api_invoke | Invoke an EXACT signature previously discovered by api_describe. Args: primitive, arrays/lists, workspace File path or {ref:handle}. Mutations may bypass undo; inspect documentation first. |
| api_construct | Construct a native object using exact discovered constructor signature; object returned as session ref |
| api_field | Read exact previously discovered native field, returning primitive or object ref |
| api_items | Paginate arrays, lists, sets or maps returned by native methods |
| api_release | Release session object refs no longer needed |
| api_field_set | Set a previously discovered non-final native field. Advanced escape hatch; may bypass undo and propagation. Use typed tools when available. |
| native_windows | Read Swing window/dialog trees for this Logisim JVM, including actual controls and handles |
| native_widget | Operate a discovered native Logisim widget: click button, set text, select combo/tab/list, set spinner, front window. Click is queued; observe results with native_windows. |
| simulation_ticks | Synchronously execute a fixed number of clock ticks and settle after each; automatic ticking must be disabled |
| simulation_control | Native simulation status/run/pause, tick, step, reset, automatic ticking and frequency. step/reset are asynchronous; poll status or propagate before dependent reads. |
| circuit_undo | Undo the latest file-affecting project action; simulated values are not undoable |
| circuit_statistics | Read native simple, unique and recursive component statistics |
| selection_edit | Native selection and clipboard: select components, copy/cut/paste/drop/duplicate/delete/move, or read. Paste remains floating until move/drop. |
| application_preferences | Read all native preference monitors or set one exact key with its correct value type; settings persist in Logisim |
| memory_export_hex | Export RAM/ROM range as native v2.0 raw hexadecimal file; does not overwrite |
| memory_import_hex | Load native v2.0 raw hex data (including count*word runs) into RAM/ROM; validate full file first |
| api_classes | Search all 610 packaged top-level com.cburch classes for API discovery |
| manual_search | Search all 129 bundled English manual pages, including all libraries and menus |
| manual_read | Read one exact bundled manual page returned by manual_search |
| source_search | Search actual Java source bundled in this exact Logisim executable; returns source paths and matching line numbers |
| source_read | Read a bounded line range from a bundled Java source path returned by source_search |
| cli_verify | Run classic Logisim headless verification with bounded timeout. Supports table/halt/speed/stats/tty, RAM -load, library -sub and keyboard stdin. Needs a self-terminating harness with halt output for normal completion. |

Resources: 129 manual pages, logisim://api/classes, logisim://guidance/agents.
