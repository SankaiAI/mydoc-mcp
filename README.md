# mydocs-mcp

**Personal Document Intelligence MCP Server**

> A Model Context Protocol server that enables AI coding agents like Claude Code to access and leverage your personal historical documents for intelligent template generation and pattern recognition.

---

## 🎯 **What is mydocs-mcp?**

mydocs-mcp is the **first-ever MCP server** designed specifically for personal document intelligence. Instead of creating project documents from scratch every time, AI agents can now:

- 🔍 **Search your document history** to find similar past work
- 🧠 **Learn your writing patterns** and document structures  
- 📝 **Generate templates** based on your successful projects
- ⚡ **Accelerate development** by 60-80% through intelligent document reuse

## 🆚 **mydocs-mcp vs Traditional Claude Code File Lookup**

| **Traditional Claude Code** | **mydocs-mcp** |
|---|---|
| 🗂️ **Manual file discovery** - You must provide exact paths | 🔍 **Intelligent file discovery** - Automatically finds relevant documents |
| 🧠 **No session memory** - Forgets previous work each session | 💾 **Persistent learning** - Remembers and builds on past interactions |
| 🔤 **Keyword matching** - Basic file pattern searches | 🧠 **Semantic understanding** - AI-powered meaning-based search |
| 🔄 **No pattern recognition** - Can't identify document relationships | 📈 **Pattern recognition** - Learns your document styles and evolution |
| ⏱️ **Manual context** - You must remember and specify file locations | 🤖 **Automatic context** - AI proactively suggests relevant documents |
| 📄 **Generic assistance** - Same approach for every user | 🎯 **Personal intelligence** - Adapts to YOUR specific documentation patterns |

### **Real-World Example:**
```
🔴 Traditional: "Create API docs like the good one I wrote before"
   → "Where is that document located?" 
   → User must remember: "C:\Projects\OldApp\docs\api.md"
   → Reads that one document, creates based on single example (10-15 minutes)

🟢 mydocs-mcp: "Create API docs like my best ones"  
   → Automatically finds your top 5 API docs across ALL projects
   → Analyzes patterns from your most successful documentation
   → Creates personalized template based on proven patterns (2-3 minutes)
```

---

## ✨ **Unique Features**

### 🏆 **First-Mover Advantages**
- **ONLY** MCP server that learns from personal document history
- **ONLY** solution providing template generation from your past work
- **ONLY** cross-project institutional knowledge preservation system

### 🔒 **Privacy-First Design**
- **Local-only processing** by default (documents never leave your machine)
- **No cloud dependencies** for core functionality
- **Enterprise-grade security** with optional encryption
- **Complete user data control** and ownership

### 🧠 **Intelligent Pattern Recognition**
- **Semantic similarity matching** - finds documents with similar meaning, not just keywords
- **Personal writing style learning** - adapts to your specific documentation patterns
- **Cross-document pattern extraction** - identifies common structures across projects
- **Context-aware recommendations** - suggests relevant documents based on current work

---

## 🚀 **Quick Start**

### **3-Day MVP Installation** (Current Phase)
*Coming soon - currently in development*

### **What's Available Now**
- ✅ Complete project documentation and requirements
- ✅ Technical architecture and implementation plan
- ✅ 3-day development roadmap and scope
- ✅ Change management system for development

---

## 📁 **Project Structure**

```
mydocs-mcp/
├── README.md                    # This file
├── CLAUDE.md                   # Rules for AI agents working on this project
├── docs/                       # Documentation
│   ├── PersonalDocAgent_MCP_PRD.md      # Product Requirements Document
│   ├── PROJECT_STRUCTURE.md             # Technical architecture
│   ├── project-management/              # Project management docs
│   │   ├── PROJECT_SCOPE_3DAY.md       # 3-day delivery scope
│   │   └── CHANGES.md                   # Change tracking log
│   └── templates/                       # Document templates
│       ├── CHANGE_REQUEST_TEMPLATE.md
│       └── TECHNICAL_DESIGN_CHANGE_TEMPLATE.md
├── src/                        # Source code (coming soon)
├── tests/                      # Test suite (coming soon)
├── config/                     # Configuration files (coming soon)
├── docker/                     # Docker deployment (coming soon)
├── scripts/                    # Development scripts (coming soon)
├── examples/                   # Usage examples (coming soon)
└── data/                       # Local data storage (coming soon)
```

---

## 📋 **Current Status**

### **✅ Completed (Planning Phase)**
- [x] **Product Requirements** - Complete PRD with competitive analysis
- [x] **Technical Architecture** - Detailed implementation plan
- [x] **3-Day Scope** - Realistic MVP delivery timeline
- [x] **Change Management** - Comprehensive documentation and approval processes
- [x] **Project Structure** - Organized directory structure for development

### **🔄 In Progress (Development Phase)**
- [ ] **Core MCP Server** - Basic MCP protocol implementation
- [ ] **Document Indexing** - Local file indexing and metadata storage
- [ ] **Search Engine** - Keyword-based document search
- [ ] **MCP Tools** - `searchDocuments`, `getDocument`, `indexDocument`

### **📅 Planned (Future Phases)**
- [ ] **Semantic Search** - AI-powered similarity matching
- [ ] **Template Generation** - Pattern extraction and template creation
- [ ] **Advanced Document Types** - PDF, JSON, YAML support
- [ ] **HTTP+SSE Transport** - Remote MCP server capability

---

## 📖 **Documentation**

### **For Users**
- [Product Overview](docs/PersonalDocAgent_MCP_PRD.md) - Complete product requirements and features
- [Technical Architecture](docs/PROJECT_STRUCTURE.md) - Implementation details and architecture

### **For Developers**
- [3-Day Development Scope](docs/project-management/PROJECT_SCOPE_3DAY.md) - Current development timeline and deliverables
- [Change Log](docs/project-management/CHANGES.md) - All project changes and their impacts
- [AI Agent Rules](CLAUDE.md) - Guidelines for Claude Code and other AI agents

### **For Contributors**
- [Change Request Template](docs/templates/CHANGE_REQUEST_TEMPLATE.md) - How to request scope/timeline changes
- [Technical Design Template](docs/templates/TECHNICAL_DESIGN_CHANGE_TEMPLATE.md) - How to document technical changes

---

## 🎯 **Target Use Cases**

### **Primary Users**
- **Software developers** using AI coding agents like Claude Code
- **Technical leads** who frequently create project documentation
- **Product managers** who need consistent document formatting

### **Common Scenarios**
- 📝 **Creating PRDs**: Find similar product requirements from past projects
- 🔧 **Writing Technical Specs**: Reference architectural decisions from previous work  
- 📊 **Generating Reports**: Use templates from successful project deliverables
- 🤖 **Defining AI Agents**: Reuse subagent definitions with proven patterns

---

## ⚡ **Performance Goals**

- **60-80% reduction** in document creation time
- **Sub-200ms search responses** for immediate results
- **Incremental indexing** with no full reprocessing
- **Works with existing workflows** - no file reorganization required

---

## 🔧 **Technology Stack**

### **Current MVP (3-Day Delivery)**
- **Language**: Python 3.11+
- **MCP Protocol**: Official `mcp` Python package
- **Storage**: SQLite for metadata, file system for documents
- **Search**: Basic keyword matching and filtering
- **Transport**: STDIO only for local development
- **Deployment**: Docker container for easy setup

### **Future Enhancements**
- **Vector Search**: ChromaDB or FAISS for semantic similarity
- **AI Embeddings**: OpenAI Ada-002 or local alternatives
- **Production Storage**: PostgreSQL for scalability
- **Remote Access**: HTTP+SSE transport for cloud deployment

---

## 🤝 **Contributing**

### **Development Process**
1. **Read Documentation**: Start with [CLAUDE.md](CLAUDE.md) for development rules
2. **Check Scope**: Verify changes align with [3-day scope](docs/project-management/PROJECT_SCOPE_3DAY.md)
3. **Log Changes**: Update [CHANGES.md](docs/project-management/CHANGES.md) for any modifications
4. **Follow Templates**: Use provided templates for formal changes

### **Change Management**
- **Low Impact Changes**: Code refactoring, optimization → Proceed freely
- **Medium Impact Changes**: Technical approach, architecture → Log in CHANGES.md
- **High Impact Changes**: Scope, timeline, deliverables → Require formal approval

---

## 📊 **Project Timeline**

### **3-Day MVP Development**
- **Day 1**: MCP server foundation, document indexing, basic tools
- **Day 2**: Search engine, Docker setup, integration testing
- **Day 3**: Demo preparation, documentation, final delivery

### **Future Roadmap**
- **Phase 2**: Semantic search and AI-powered features
- **Phase 3**: Advanced document types and remote deployment
- **Phase 4**: Enterprise features and team collaboration

---

## 📞 **Support & Contact**

### **Project Status**
- **Current Phase**: 3-Day MVP Development
- **Timeline**: 72 hours from development start
- **Status**: Documentation complete, ready for development

### **Getting Help**
- **Technical Issues**: Check [CHANGES.md](docs/project-management/CHANGES.md) for recent updates
- **Scope Questions**: Review [PROJECT_SCOPE_3DAY.md](docs/project-management/PROJECT_SCOPE_3DAY.md)
- **Change Requests**: Use [templates](docs/templates/) for formal change requests

---

## 📄 **License**

*License to be determined during development phase*

---

## 🙏 **Acknowledgments**

- **Anthropic** - For the Model Context Protocol specification
- **MCP Community** - For existing server implementations and best practices
- **AI Development Community** - For pioneering AI-assisted development workflows

---

**Ready to revolutionize your document workflow with AI-powered personal intelligence? Let's build the future of intelligent document management together! 🚀**

---

*Last Updated: September 3, 2025*  
*Version: 1.0 (Pre-Development)*