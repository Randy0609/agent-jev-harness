# Third-party components

The original adapter code in this repository is MIT licensed. Upstream projects retain their own authorship and licenses. No affiliation or endorsement is implied.

| Project | Pinned source / package | License copy | Integration |
|---|---|---|---|
| [qkal/Canny](https://github.com/qkal/Canny) | `d927d2606b07ce990fa4bef8908a27d8d32db1e1` | [MIT](integrations/licenses/canny.txt) | Unmodified source submodule; ledger library and CLI |
| [itsmostafa/typesafe-mcp](https://github.com/itsmostafa/typesafe-mcp) | `d4c110c7edd82127a4ca962c9d60fb96f748eb6e`, v0.4.2 release | [MIT](integrations/licenses/typesafe-mcp.txt) | Unmodified submodule; checksum-pinned official binary |
| [jkudish/jev-mcp](https://github.com/jkudish/jev-mcp) | `42aa7ff79cc2b269f1f1a6893fe6e027a166fed7` | [MIT](integrations/licenses/jev-mcp.txt) | Unmodified source submodule; MCP tool adapter |
| [sharziki/semdecide](https://github.com/sharziki/semdecide) | `33cf5c03c50e02e59df3f3ea81f0650f6b791545` | [MIT](integrations/licenses/semdecide.txt) | Unmodified source submodule; CLI and batch library |
| [vercel-labs/json-render](https://github.com/vercel-labs/json-render) | `@json-render/core` + `@json-render/react` 0.21.0 | [Apache-2.0](integrations/licenses/json-render.txt) | Official npm packages, package-lock integrity pinned |

Our adapters, receipt format, fixed dashboard catalog, and business examples are local additions; upstream source files were not modified. Upstream submodules retain their full license files. npm dependencies retain their own notices in installed packages; exact transitive dependencies are recorded in the respective lockfiles. Model weights and hosted provider services are not included.
