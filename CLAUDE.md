# CLAUDE.md - Rules for AI Coding Agent Documentation Management
## mydocs-mcp Project

---

## 🎯 **PRIMARY DIRECTIVE**

**Claude Code and other AI agents working on mydocs-mcp MUST follow these documentation rules strictly. These rules ensure project consistency, proper change tracking, and successful delivery within the 3-day timeline.**

---

## 📋 **DOCUMENTATION HIERARCHY**

### **🔒 IMMUTABLE DOCUMENTS** (Cannot change without formal approval)
1. **docs/project-management/PROJECT_SCOPE_3DAY.md** - The project contract
2. **Core deliverables and timeline** in scope document
3. **Success criteria and metrics** defined in scope
4. **IN SCOPE vs OUT OF SCOPE** boundaries

### **📝 UPDATEABLE DOCUMENTS** (Can modify with tracking)
1. **docs/PROJECT_STRUCTURE.md** - Implementation details
2. **docs/PersonalDocAgent_MCP_PRD.md** - Technical specifications  
3. **README.md** - Usage instructions
4. **API documentation** - Technical references

---

## 🤖 **AGENT INTEGRATION**

### **Available Specialized Agents & Tools**

#### **📋 Project Management Agents:**
- **project-coordinator**: Use when there's a gap between user suggestions and technical best practices, or when validating implementation approaches
- **project-documentor**: Use when creating or updating project management documentation, requirements, specifications, or process documents
- **draw.io MCP**: Use for creating system diagrams, architecture diagrams, flowcharts, and visual documentation

#### **💻 Expert Coding Agents:**
- **mcp-server-architect**: Expert in MCP server framework, protocol implementation, transport layers, and server architecture
- **storage-engineer**: Expert in database design, SQLite implementation, data modeling, and storage optimization
- **tools-developer**: Expert in MCP tools implementation, tool interface design, and MCP protocol tool development
- **search-engineer**: Expert in search algorithms, query processing, relevance ranking, and search performance optimization
- **testing-specialist**: Expert in comprehensive testing, test automation, performance validation, and quality assurance

#### **🎯 When to Use Each Agent:**

**Project Management:**
- **project-coordinator**: Technical decision mediation, implementation approach validation, user intent clarification, trade-off analysis
- **project-documentor**: Project documentation needs, scope changes requiring documentation updates, technical specifications, process documentation
- **draw.io**: System architecture design, data flow diagrams, component relationships, user journey flows, technical process visualization

**Development Specialists:**
- **mcp-server-architect**: MCP server core development, protocol compliance, transport implementation, server lifecycle management
- **storage-engineer**: Database schema design, SQLite optimization, document indexing, storage performance, data modeling
- **tools-developer**: MCP tools implementation (searchDocuments, getDocument, indexDocument), tool interface design, parameter validation
- **search-engineer**: Search algorithm development, query processing, relevance scoring, search performance optimization
- **testing-specialist**: Unit testing, integration testing, performance benchmarks, quality assurance, test automation

### **Agent & Tool Usage Guidelines**

#### **Project Management Workflow:**
```
WHEN implementation approach unclear or disputed:
1. Use project-coordinator agent to evaluate options
2. Present user intent and technical constraints
3. Get recommendation on optimal approach
4. Document decision and rationale

WHEN creating project documentation:
1. Use project-documentor agent for comprehensive documentation tasks
2. Use draw.io MCP for visual system design and architecture diagrams
3. Provide context about mydocs-mcp project specifics
4. Reference existing documentation structure in docs/ folder
5. Ensure consistency with established templates and formats

WHEN creating visual documentation:
1. Use draw.io MCP for all diagram creation needs
2. Save diagrams in docs/diagrams/ folder
3. Include both .drawio source files and exported .png/.svg images
4. Reference diagrams in relevant documentation
5. Use consistent naming: mydocs-mcp-[diagram-type]-[date].drawio
```

#### **Development Specialist Workflow:**
```
WHEN starting MCP server development:
1. Use mcp-server-architect for server foundation and protocol implementation
2. Focus on MCP protocol compliance and transport layer setup
3. Establish tool registry system and server lifecycle management
4. Coordinate with other agents through clean interface contracts

WHEN working on data storage:
1. Use storage-engineer for all database design and SQLite implementation
2. Focus on schema design, indexing strategy, and query optimization
3. Ensure sub-200ms query performance and data integrity
4. Coordinate with search and tools agents through storage interfaces

WHEN implementing MCP tools:
1. Use tools-developer for all MCP tool implementation (searchDocuments, getDocument, indexDocument)
2. Focus on parameter validation, error handling, and tool performance
3. Ensure MCP protocol compliance and clean tool interfaces
4. Coordinate with storage and search agents for backend functionality

WHEN developing search capabilities:
1. Use search-engineer for search algorithm and query processing implementation
2. Focus on relevance ranking, performance optimization, and result formatting
3. Ensure sub-200ms search response times and search quality
4. Coordinate with storage layer for search index optimization

WHEN implementing testing:
1. Use testing-specialist for all testing activities and quality assurance
2. Focus on comprehensive test coverage, performance validation, and integration testing
3. Ensure >95% code coverage and sub-200ms performance validation
4. Coordinate with all agents for component and integration testing
```

#### **Agent Collaboration Patterns:**
```
CRITICAL DEPENDENCIES (must complete in order):
1. mcp-server-architect → (foundation for all other development)
2. storage-engineer → (required for tools and search)
3. tools-developer + search-engineer → (can work in parallel)
4. testing-specialist → (validates all components)

PARALLEL DEVELOPMENT OPPORTUNITIES:
- tools-developer + search-engineer (both use storage interfaces)
- All agents can work with testing-specialist for continuous testing
- project-documentor can update documentation as development progresses
```

---

## 🚦 **CHANGE MANAGEMENT RULES**

### **Rule 1: ALWAYS Check Scope First**
```
BEFORE making ANY change:
1. Read docs/project-management/PROJECT_SCOPE_3DAY.md 
2. Verify change aligns with IN SCOPE items
3. If change affects OUT OF SCOPE items → STOP and request approval
```

### **Rule 2: Document Changes Immediately**
```
EVERY medium/high impact change must be documented using individual change files:

FOR MEDIUM/HIGH IMPACT CHANGES:
1. Copy docs/templates/INDIVIDUAL_CHANGE_TEMPLATE.md
2. Create: docs/project-management/changes/CHANGE-XXX-[brief-description].md
3. Fill in comprehensive change details using template
4. Update docs/project-management/CHANGES_INDEX.md with new entry

FOR LOW IMPACT CHANGES (code tweaks, minor updates):
- Log directly in docs/project-management/CHANGES_INDEX.md summary
- No individual change file required
```

### **Rule 3: Scope Changes Require Approval**
```
IF change affects:
- Timeline (extends beyond 72 hours)
- Core deliverables
- Success criteria
- IN/OUT OF SCOPE boundaries

THEN:
1. Create formal change request using docs/templates/CHANGE_REQUEST_TEMPLATE.md
2. Create individual change file with status "PENDING APPROVAL"
3. Update docs/project-management/CHANGES_INDEX.md with pending change entry
4. Do NOT implement until approved
```

---

## 📄 **REQUIRED ACTIONS FOR EACH CHANGE TYPE**

### **LOW IMPACT: Code Implementation Changes**
**Examples**: Variable names, function structure, code organization
**Required Actions**:
- ✅ Implement freely
- ✅ Update code comments
- ✅ Log in git commit messages
- ❌ No formal documentation needed

### **MEDIUM IMPACT: Technical Approach Changes**  
**Examples**: Database choice, library selection, architecture patterns
**Required Actions**:
- ✅ Update docs/PROJECT_STRUCTURE.md
- ✅ Log change in docs/project-management/CHANGES_INDEX.md or create individual change file for medium/high impact changes
- ✅ Update relevant technical docs
- ✅ Notify in commit message

### **HIGH IMPACT: Scope/Timeline Changes**
**Examples**: Adding features, extending deadline, changing core deliverables
**Required Actions**:
- ❌ STOP implementation
- ✅ Create CHANGE_REQUEST_XXX.md
- ✅ Create individual change file with status "PENDING APPROVAL"
- ✅ Wait for human approval before proceeding

---

## 📋 **MANDATORY DOCUMENTATION UPDATES**

### **🚀 CRITICAL: Read DEVELOPMENT_STATUS.md First**
**EVERY Claude Code session must start by reading `docs/project-management/DEVELOPMENT_STATUS.md`**
- This is your SOURCE OF TRUTH for current progress
- Tells you exactly what to work on next
- Provides complete context for session continuity

### **When Starting Development Session:**
1. ✅ **FIRST**: Read `docs/project-management/DEVELOPMENT_STATUS.md` for current context
2. ✅ Update DEVELOPMENT_STATUS.md "Current Development Context" with session start
3. ✅ Create `README.md` with setup instructions (if first session)
4. ✅ Update `docs/project-management/CHANGES_INDEX.md` with "Development Started" (if first session)
5. ✅ Use **project-documentor agent** for comprehensive documentation tasks
6. ✅ **ANALYZE FIRST** - Review docs/SYSTEM_DESIGN_REQUIREMENTS.md to understand what diagrams are needed
7. ✅ Use **draw.io MCP** to create system architecture diagrams and component designs

### **After Completing Each Task (MANDATORY):**
1. ✅ **IMMEDIATELY** update `docs/project-management/DEVELOPMENT_STATUS.md`:
   - Change task status from ⏳ PENDING to ✅ COMPLETE
   - Add completion timestamp
   - Add any notes about issues or discoveries
   - Update progress metrics
2. ✅ Update "Current Development Context" section with what you just completed
3. ✅ Update "Immediate Next Steps" with next task to work on

### **During Daily Development:**
1. ✅ **EVERY 2-4 hours**: Update DEVELOPMENT_STATUS.md with current progress
2. ✅ Create individual change files for medium/high impact changes, update CHANGES_INDEX.md for all changes
3. ✅ Keep `docs/PROJECT_STRUCTURE.md` current with actual implementation
4. ✅ Update API documentation as tools are implemented
5. ✅ Use **project-documentor agent** when creating technical specifications or process documents
6. ✅ **BEFORE creating diagrams** - Analyze what has changed and what needs visual representation
7. ✅ Use **draw.io MCP** for technical diagrams, data flow charts, and component relationships

### **When Completing Daily Milestones:**
1. ✅ **MANDATORY**: Update DEVELOPMENT_STATUS.md with daily completion status
2. ✅ Update `docs/project-management/CHANGES_INDEX.md` with progress summary
3. ✅ Update scope document with milestone completion status
4. ✅ Verify documentation matches actual implementation
5. ✅ Use **project-documentor agent** for milestone documentation and project summaries
6. ✅ Use **draw.io MCP** to create final system diagrams and deployment architecture

### **End of Session (Before Stopping):**
1. ✅ **CRITICAL**: Update DEVELOPMENT_STATUS.md "Session Handoff Notes" section
2. ✅ Document current work state and next immediate priority
3. ✅ Update any blockers or issues encountered
4. ✅ Ensure next Claude Code session knows exactly what to do

---

## 📄 **DOCUMENT UPDATE WORKFLOW RULES**

### **🔒 IMMUTABLE DOCUMENTS (NEVER UPDATE without formal approval)**
- `docs/project-management/PROJECT_SCOPE_3DAY.md` - The project contract
- Core deliverables and timeline in scope document
- Success criteria and metrics defined in scope
- IN SCOPE vs OUT OF SCOPE boundaries

### **📊 REAL-TIME UPDATE DOCUMENTS (Update constantly during development)**
- `docs/project-management/DEVELOPMENT_STATUS.md` - **CRITICAL: Update after every task**
- `docs/project-management/CHANGES_INDEX.md` - Update with all changes
- Session continuity notes and current context

### **🔄 REGULAR UPDATE DOCUMENTS (Update as implementation progresses)**
- `docs/PROJECT_STRUCTURE.md` - Keep current with actual code structure
- `docs/TECHNICAL_ARCHITECTURE.md` - Update if major technical changes occur
- API documentation files - Update as tools are implemented
- README.md - Update as features are completed

### **📝 MILESTONE UPDATE DOCUMENTS (Update at major milestones)**
- `docs/PersonalDocAgent_MCP_PRD.md` - Update if requirements evolve
- Progress summaries and status reports
- Integration testing results and system validation

### **🆕 CREATE AS NEEDED DOCUMENTS**
- Individual change files in `docs/project-management/changes/`
- API reference documentation
- Troubleshooting guides
- Deployment documentation

### **UPDATE TRIGGERS AND FREQUENCY**

#### **EVERY TASK COMPLETION** (Mandatory):
```
MUST UPDATE: docs/project-management/DEVELOPMENT_STATUS.md
- Change task status to ✅ COMPLETE
- Add timestamp and notes
- Update progress metrics
- Update "Current Development Context"
```

#### **EVERY 4-HOUR BLOCK** (High Priority):
```
SHOULD UPDATE:
- DEVELOPMENT_STATUS.md with detailed progress
- CHANGES_INDEX.md if any significant changes occurred
- PROJECT_STRUCTURE.md if code structure evolved
```

#### **DAILY MILESTONES** (Required):
```
MUST UPDATE:
- DEVELOPMENT_STATUS.md with daily completion status
- CHANGES_INDEX.md with daily summary
- Any documentation affected by day's development
```

#### **MAJOR TECHNICAL CHANGES** (As Needed):
```
SHOULD UPDATE:
- TECHNICAL_ARCHITECTURE.md if tech stack changes
- PROJECT_STRUCTURE.md if architecture changes
- Create individual change file if impact is Medium/High
```

#### **SESSION END** (Before Stopping - Critical):
```
MUST UPDATE:
- DEVELOPMENT_STATUS.md "Session Handoff Notes"
- Current work state and immediate next priority
- Any blockers or issues for next session
```

### **WORKFLOW DECISION MATRIX**

| **Action** | **Update DEVELOPMENT_STATUS.md** | **Update CHANGES_INDEX.md** | **Update PROJECT_STRUCTURE.md** | **Create Change File** |
|------------|----------------------------------|------------------------------|----------------------------------|----------------------|
| **Complete a task** | ✅ MANDATORY | ❌ No | ❌ No | ❌ No |
| **Complete 4-hour block** | ✅ MANDATORY | ⚠️ If changes made | ⚠️ If structure changed | ❌ No |
| **Daily milestone** | ✅ MANDATORY | ✅ MANDATORY | ⚠️ If structure changed | ❌ No |
| **Technical decision change** | ✅ Update context | ✅ MANDATORY | ✅ MANDATORY | ✅ If Medium/High impact |
| **Add/remove feature** | ✅ MANDATORY | ✅ MANDATORY | ✅ MANDATORY | ✅ MANDATORY |
| **Bug fix (minor)** | ✅ Update progress | ❌ No | ❌ No | ❌ No |
| **Bug fix (major)** | ✅ Update progress | ✅ MANDATORY | ⚠️ If affects structure | ✅ If High impact |
| **Session start** | ✅ Update context | ❌ No | ❌ No | ❌ No |
| **Session end** | ✅ MANDATORY | ❌ No | ❌ No | ❌ No |

---

## 🔍 **CHANGE VALIDATION CHECKLIST**

Before implementing ANY change, Claude Code must verify:

### **Scope Validation:**
- [ ] Change is listed in IN SCOPE section
- [ ] Change does NOT affect OUT OF SCOPE boundaries
- [ ] Change does NOT extend 3-day timeline
- [ ] Change supports core success criteria

### **Documentation Impact:**
- [ ] Identify which documents need updates
- [ ] Create individual change file for medium/high impact changes or update CHANGES_INDEX.md for low impact
- [ ] Update affected technical documents
- [ ] Verify documentation consistency

### **Implementation Safety:**
- [ ] Change does not break existing functionality
- [ ] Change aligns with MCP protocol requirements
- [ ] Change supports 3-day delivery timeline

---

## 📝 **REQUIRED DOCUMENT UPDATES BY CHANGE TYPE**

| Change Type | Change Documentation | docs/PROJECT_STRUCTURE.md | docs/PRD | docs/project-management/SCOPE | Approval Needed |
|---|---|---|---|---|---|
| **Code refactoring** | ✅ | ❌ | ❌ | ❌ | ❌ |
| **Library choice** | ✅ | ✅ | ✅ | ❌ | ❌ |
| **Architecture change** | ✅ | ✅ | ✅ | ❌ | ⚠️ Maybe |
| **Add feature (in scope)** | ✅ | ✅ | ✅ | ❌ | ❌ |
| **Add feature (out of scope)** | ✅ | ❌ | ❌ | ❌ | ⚠️ **REQUIRED** |
| **Timeline extension** | ✅ | ❌ | ❌ | ❌ | ⚠️ **REQUIRED** |
| **Change deliverables** | ✅ | ❌ | ❌ | ✅ | ⚠️ **REQUIRED** |

---

## 🚨 **CRITICAL RESTRICTIONS**

### **NEVER DO THESE WITHOUT APPROVAL:**
- ❌ Change the 3-day timeline
- ❌ Add features from OUT OF SCOPE list  
- ❌ Remove features from IN SCOPE list
- ❌ Change core MCP tool specifications
- ❌ Change success criteria or metrics
- ❌ Modify project objectives

### **ALWAYS DO THESE:**
- ✅ Check scope document before implementing
- ✅ Create individual change files for medium+ impact changes
- ✅ Keep documentation current with implementation
- ✅ Verify MCP protocol compliance
- ✅ Focus on 3-day delivery timeline

---

## 📋 **CHANGE REQUEST PROCESS**

### **Step 1: Identify Need for Change**
```
IF change affects scope/timeline/deliverables:
  → Create CHANGE_REQUEST_XXX.md
  → Create individual change file with status "PENDING APPROVAL"  
  → STOP implementation
```

### **Step 2: Document Change Request**
Use template: `docs/templates/CHANGE_REQUEST_TEMPLATE.md`

### **Step 3: Wait for Approval**
```
Do NOT implement scope changes without explicit human approval
Continue with other IN SCOPE work while waiting
```

### **Step 4: Implement After Approval**
```
IF approved:
  → Update affected documents
  → Update individual change file status to "APPROVED - IMPLEMENTED"
  → Proceed with implementation

IF rejected:
  → Update individual change file status to "REJECTED"
  → Continue with original scope
```

---

## 🎯 **SUCCESS METRICS FOR DOCUMENTATION**

Claude Code's documentation management will be considered successful if:

1. ✅ **Zero scope violations**: No OUT OF SCOPE features implemented
2. ✅ **Complete change tracking**: All changes tracked in CHANGES_INDEX.md with detailed individual change files
3. ✅ **Documentation consistency**: All docs reflect actual implementation  
4. ✅ **Timeline adherence**: 3-day deadline maintained
5. ✅ **Approval compliance**: All required approvals obtained before implementation

---

## 🔄 **DAILY DOCUMENTATION ROUTINE**

### **Every Development Session:**
1. **Start**: Read current docs/project-management/CHANGES_INDEX.md to understand recent modifications
2. **During**: Log any medium/high impact changes immediately
3. **End**: Update relevant technical documentation
4. **Review**: Verify scope compliance before committing code

### **Daily Status Update Required:**
```markdown
## Daily Progress - Day X
- **Completed**: [List of completed tasks]
- **In Progress**: [Current work]
- **Changes Made**: [Reference individual change files in docs/project-management/changes/]  
- **Scope Status**: ✅ On track / ⚠️ Risk / ❌ Scope violation
- **Timeline Status**: ✅ On schedule / ⚠️ Risk / ❌ Behind schedule
```

---

## 🤖 **AGENT COLLABORATION GUIDELINES**

### **When to Use project-coordinator Agent:**
```
USE project-coordinator FOR:
✅ User suggests implementation that conflicts with best practices
✅ Multiple valid technical approaches need evaluation
✅ User's understanding and technical complexity need bridging
✅ Implementation decision will impact project timeline or scope
✅ Trade-offs between simplicity and robustness need discussion
✅ Preventing miscommunication before implementation begins

PROVIDE project-coordinator WITH:
✅ User's suggested approach and intent
✅ Technical constraints and best practices
✅ Project scope and timeline context
✅ Specific concerns about the implementation
```

### **When to Use project-documentor Agent:**
```
USE project-documentor FOR:
✅ Creating technical specifications
✅ Updating project requirements documentation  
✅ Creating milestone summaries and progress reports
✅ Documenting scope changes or technical decisions
✅ Creating comprehensive project documentation

PROVIDE project-documentor WITH:
✅ Current project context and status
✅ Specific documentation requirements
✅ Target audience information
✅ Reference to existing documentation structure
```

### **When to Use draw.io MCP:**
```
USE draw.io MCP FOR:
✅ System architecture diagrams
✅ Component relationship diagrams  
✅ Data flow diagrams
✅ User interaction flows
✅ MCP protocol communication diagrams
✅ Database schema diagrams
✅ Deployment architecture diagrams

DIAGRAM NAMING CONVENTION:
✅ mydocs-mcp-architecture-2025-09-03.drawio
✅ mydocs-mcp-dataflow-2025-09-03.drawio
✅ mydocs-mcp-components-2025-09-03.drawio
✅ mydocs-mcp-deployment-2025-09-03.drawio
```

### **Agent & Tool Handoff Protocol:**
```
WHEN calling project-documentor:
1. Summarize current project status
2. Specify exact documentation need
3. Reference relevant existing documents
4. Clarify timeline and scope constraints
5. Ensure agent has access to docs/ folder structure

WHEN using draw.io MCP:
1. **ANALYSIS PHASE** - Review and plan what needs to be drawn:
   a. Analyze current project context and documentation gaps
   b. Identify specific components, relationships, or processes to visualize
   c. Determine which diagram type(s) would be most effective
   d. List key elements that must be included in the diagram
   e. Consider target audience (technical/non-technical stakeholders)
2. **PLANNING PHASE** - Create diagram specification:
   a. Define diagram scope and boundaries
   b. List all components/elements to include
   c. Identify relationships and connections to show
   d. Plan diagram layout and organization
3. **CREATION PHASE** - Use draw.io MCP to create diagram:
   a. Reference existing system design context
   b. Create both source (.drawio) and export (.png/.svg) files
   c. Save in docs/diagrams/ folder with proper naming
4. **INTEGRATION PHASE** - Connect diagram to documentation:
   a. Reference diagram in relevant documentation
   b. Add explanatory text connecting diagram to project context
   c. Update CHANGES_INDEX.md with diagram creation summary or create individual change file if significant
```

---

## 📞 **ESCALATION PROTOCOL**

### **When to Stop and Ask for Help:**
1. 🚨 **Immediate Stop Scenarios**:
   - Change would extend timeline beyond 3 days
   - Change requires OUT OF SCOPE features
   - Change affects core deliverables
   - Technical blocker prevents scope completion

2. 🔄 **Continue with Caution**:
   - Technical implementation choices
   - Code organization decisions  
   - Library selection within constraints

3. ✅ **Proceed Freely**:
   - Code refactoring and optimization
   - Documentation improvements (use project-documentor agent)
   - Bug fixes and quality improvements

---

**Remember: When in doubt about scope impact, ASK FOR CLARIFICATION rather than assume. It's better to request approval for unnecessary changes than to violate scope accidentally.**

---

**Document Version**: 1.0  
**Last Updated**: September 3, 2025  
**For**: mydocs-mcp 3-day development sprint