# CLAUDE.md - Rules for AI Coding Agent Documentation Management
## mydocs-mcp Project

---

## 🎯 **PRIMARY DIRECTIVE**

**Claude Code and other AI agents working on mydocs-mcp MUST follow these documentation rules strictly. These rules ensure project consistency, proper change tracking, and successful delivery within the 3-day timeline.**

---

## 🛡️ **MANDATORY USER REQUEST VALIDATION PROCESS**

### **CRITICAL: ALL User Requests Must Be Analyzed FIRST**

**BEFORE implementing ANY user request, Claude Code MUST:**

1. **IMMEDIATELY call project-coordinator agent to analyze the request**
   - Even if the request seems straightforward
   - Even if the user insists on immediate implementation
   - Even if it appears to be a minor change
   - NO EXCEPTIONS to this rule

2. **Provide project-coordinator with:**
   - The exact user request (verbatim)
   - Current project context and status
   - Technical implications of the request
   - Potential conflicts with best practices
   - Impact on scope, timeline, or architecture

3. **Wait for project-coordinator's analysis which will:**
   - ✅ Validate if request aligns with project goals
   - ❌ Identify conflicts with best practices
   - ⚠️ Highlight potential risks or issues
   - 🔄 Suggest alternative approaches if needed
   - 📋 Determine proper implementation path

4. **Based on project-coordinator's response:**
   - **If APPROVED**: Proceed with implementation
   - **If CONCERNS RAISED**: Discuss with user before proceeding
   - **If REJECTED**: Explain why and offer alternatives
   - **If UNCLEAR**: Ask user for clarification

### **Examples of MANDATORY project-coordinator validation:**

```
USER: "Let's put the test file in the root directory"
CLAUDE CODE ACTION: 
1. Call project-coordinator to analyze test file location request
2. Project-coordinator identifies this violates project structure best practices
3. Respond to user with recommended tests/ folder location
4. Only proceed after alignment

USER: "Skip the database and just use JSON files"
CLAUDE CODE ACTION:
1. Call project-coordinator to analyze storage approach change
2. Project-coordinator evaluates performance and scalability impact
3. Present trade-offs to user
4. Implement only after informed decision

USER: "Just quickly add this feature"
CLAUDE CODE ACTION:
1. Call project-coordinator to analyze feature addition
2. Project-coordinator checks scope boundaries
3. Determine if feature is IN SCOPE or OUT OF SCOPE
4. Proceed only if validated or approved
```

### **NO BLIND AGREEMENT Policy:**
- ❌ NEVER automatically agree with user suggestions
- ❌ NEVER skip validation to save time
- ❌ NEVER assume user's approach is optimal
- ✅ ALWAYS validate through project-coordinator
- ✅ ALWAYS provide technical assessment
- ✅ ALWAYS protect project integrity

---

## 🔍 **CLAUDE CODE PRE-TASK DOCUMENT REVIEW PROTOCOL**

### **CRITICAL: Mandatory Document Review Before Each Development Task**

**ALL development tasks performed by Claude Code MUST begin with this mandatory document review protocol. This ensures governance consistency with subagent requirements and prevents architectural drift, performance violations, and integration conflicts.**

**NO EXCEPTIONS**: This requirement applies to ALL development tasks without exception.

---

### **MANDATORY LIGHT PROTOCOL (15-30 seconds per task)**

**BEFORE starting ANY development task, Claude Code MUST:**

#### **📋 Core Document Quick Scan (MANDATORY)**:
1. **✅ DEVELOPMENT_STATUS.md** - Current context, task priorities, session continuity
   - Check "Current Development Context" for immediate priorities
   - Verify "Immediate Next Steps" align with planned work
   - Review "Last Completed" to understand current state
   - Check for any blockers or issues from previous work

2. **✅ TECHNICAL_ARCHITECTURE.md** - Technical approach and architectural constraints
   - Review relevant sections for component being modified
   - Check performance requirements (sub-200ms targets)
   - Verify architectural decisions and design patterns
   - Confirm integration specifications and interfaces

3. **✅ PROJECT_STRUCTURE.md** - Code structure and file organization (when modifying/adding files)
   - Verify file placement follows established structure
   - Check naming conventions and organization patterns
   - Confirm component relationships and dependencies
   - Validate module hierarchy and interfaces

4. **✅ SYSTEM_DESIGN_REQUIREMENTS.md** - Design decisions and performance specifications
   - Check relevant design constraints for current task
   - Verify performance targets and quality requirements
   - Review system integration requirements
   - Confirm compliance with architectural specifications

#### **⚡ Quick Validation Checklist (MANDATORY)**:
Before proceeding with development task:
- [ ] **Current Context Verified** - Understand where project stands and what needs to be done next
- [ ] **Technical Approach Confirmed** - Implementation aligns with architectural decisions
- [ ] **Performance Targets Known** - Sub-200ms requirements and quality metrics understood
- [ ] **Integration Constraints Checked** - Component interfaces and dependencies verified
- [ ] **Scope Compliance Verified** - Task aligns with IN SCOPE items and project boundaries

---

### **PROTOCOL ENFORCEMENT**

#### **MANDATORY COMPLIANCE REQUIREMENTS**:
1. **Every Task Must Begin** with this document review protocol
2. **No Development Without Review** - Cannot start coding/implementation without completing protocol
3. **Document Current Understanding** - Reference relevant constraints and requirements during work
4. **Verify Alignment Continuously** - Check architectural compliance during implementation
5. **Update Context After Completion** - Ensure DEVELOPMENT_STATUS.md reflects current state

#### **COMPLIANCE VERIFICATION CHECKLIST**:
- [ ] **Protocol Completed** - All mandatory documents reviewed before starting work
- [ ] **Context Understood** - Current project state and priorities clear
- [ ] **Constraints Known** - Technical and architectural limitations understood
- [ ] **Performance Aware** - Sub-200ms targets and quality requirements confirmed
- [ ] **Scope Verified** - Task aligns with project boundaries and deliverables

#### **ESCALATION FOR NON-COMPLIANCE**:
```
IF Claude Code skips mandatory document review protocol:
1. STOP current work immediately
2. Complete mandatory document review protocol
3. Verify alignment with architectural requirements
4. Document any conflicts or issues discovered
5. If conflicts found, reassess approach before proceeding
```

---

### **PROTOCOL RATIONALE**

#### **Why This Protocol is Critical**:
1. **Prevents Architecture Drift** - Ensures decisions align with established technical architecture
2. **Maintains Performance Targets** - Confirms sub-200ms requirements are met consistently
3. **Ensures Scope Compliance** - Verifies work stays within project boundaries
4. **Reduces Rework** - Catches integration conflicts before they become expensive fixes
5. **Maintains Quality** - Ensures consistent standards across all development work

#### **Time Investment vs. Value**:
- **Time Cost**: 15-30 seconds per task
- **Time Saved**: Hours of potential rework from architectural conflicts
- **Quality Impact**: Significant improvement in consistency and integration quality
- **Risk Reduction**: Prevents critical path delays from integration issues

#### **Consistency with Subagent Requirements**:
This protocol ensures Claude Code follows the same governance standards it requires from all subagents, maintaining consistency across the entire development process.

---

### **SPECIALIZED PROTOCOL EXTENSIONS**

#### **For Complex Architecture Tasks**:
```
ADDITIONAL REQUIREMENTS for tasks affecting system architecture:
1. Review SYSTEM_DESIGN_REQUIREMENTS.md in detail (not just quick scan)
2. Check component interaction specifications
3. Verify performance impact assessment
4. Confirm integration testing requirements
5. Update architectural documentation if needed
```

#### **For Database/Storage Tasks**:
```
ADDITIONAL REQUIREMENTS for database and storage tasks:
1. Review schema specifications and performance requirements
2. Check data model constraints and relationships
3. Verify query performance targets (sub-200ms)
4. Confirm backup and migration requirements
5. Validate data integrity specifications
```

#### **For MCP Protocol Tasks**:
```
ADDITIONAL REQUIREMENTS for MCP protocol tasks:
1. Review MCP protocol compliance specifications
2. Check tool interface requirements and validation rules
3. Verify transport layer constraints (stdio only)
4. Confirm error handling and response formatting
5. Validate protocol version compatibility
```

---

### **PROTOCOL SUCCESS METRICS**

#### **Compliance Indicators**:
- ✅ **Zero architectural conflicts** during development
- ✅ **Performance targets maintained** - all operations sub-200ms
- ✅ **Scope violations prevented** - no OUT OF SCOPE feature implementation
- ✅ **Integration issues minimized** - clean component interfaces maintained
- ✅ **Rework cycles eliminated** - fewer architectural corrections needed

#### **Quality Improvements**:
- **Architectural Consistency** - Decisions align with established patterns
- **Performance Predictability** - Requirements met consistently across components
- **Integration Reliability** - Components work together without interface conflicts
- **Documentation Accuracy** - Implementation matches documented architecture
- **Timeline Protection** - Rework prevention keeps project on schedule

---

**CRITICAL SUCCESS FACTOR**: This Claude Code pre-task document review protocol is ESSENTIAL for maintaining architectural consistency, preventing performance violations, and ensuring successful delivery within the mydocs-mcp 3-day development sprint. ALL development tasks MUST follow this protocol without exception.

---

## 📝 **MANDATORY project-documentor USAGE RULES**

### **CRITICAL: Claude Code MUST call project-documentor for ANY documentation governance changes**

**BEFORE making changes to these document types, Claude Code MUST call project-documentor:**

#### **🔒 GOVERNANCE DOCUMENTS (ALWAYS use project-documentor):**
1. **CLAUDE.md** - This governance document itself
2. **PROJECT_SCOPE_3DAY.md** - Project contract and scope boundaries
3. **CHANGES_INDEX.md** - Change management system
4. **DEVELOPMENT_STATUS.md** - Development progress tracking
5. **Any file in docs/project-management/** - Project management processes
6. **Any file in docs/templates/** - Documentation templates and standards

#### **📋 PROCESS DOCUMENTS (ALWAYS use project-documentor):**
1. **Agent usage guidelines** - Rules for calling specialized agents
2. **Workflow documentation** - Development and documentation processes  
3. **Change management processes** - How to document and track changes
4. **Quality assurance processes** - Testing and validation procedures
5. **Project coordination processes** - Team and stakeholder communication

### **project-documentor Usage Protocol:**

```
WHEN making ANY change to governance/process documents:
1. STOP implementation immediately  
2. Call project-documentor agent FIRST
3. Provide full context of proposed change
4. Get proper documentation strategy
5. Follow project-documentor's guidance
6. Create proper change documentation
7. ONLY THEN proceed with implementation
```

### **Examples of MANDATORY project-documentor usage:**

```
SCENARIO: User asks to "update the agent rules in CLAUDE.md"
CORRECT ACTION:
1. Call project-documentor FIRST
2. Provide context and proposed changes
3. Get documentation strategy from project-documentor
4. Follow project-documentor guidance for change documentation
5. Only then implement the changes

SCENARIO: Need to update change management process
CORRECT ACTION:  
1. Call project-documentor FIRST
2. Discuss process improvement with project-documentor
3. Create proper change documentation through project-documentor
4. Update CHANGES_INDEX.md through project-documentor
5. Only then implement changes

SCENARIO: Adding new agent to the project
CORRECT ACTION:
1. Call project-documentor FIRST  
2. Document agent integration strategy with project-documentor
3. Create proper change records through project-documentor
4. Update all affected documentation through project-documentor
5. Only then begin using the new agent
```

### **EXPLICIT TRIGGERS: WHEN to Call project-documentor**

**IMMEDIATE project-documentor REQUIRED for ANY of these scenarios:**

#### **📋 Documentation Creation/Updates:**
- Creating new project management documents
- Updating technical specifications or requirements
- Writing process documentation or procedures
- Creating milestone summaries or progress reports
- Documenting scope changes or technical decisions
- Creating comprehensive project documentation

#### **🔒 Governance Changes:**
- ANY edit to CLAUDE.md (this file)
- Changes to PROJECT_SCOPE_3DAY.md process
- Updates to change management system
- Modifications to agent usage rules
- Changes to development workflow processes
- Updates to quality assurance procedures

#### **📊 Process Documentation:**
- Documenting new agent integrations
- Creating workflow documentation
- Updating development processes
- Documenting testing procedures
- Creating deployment documentation
- Updating project coordination processes

#### **📈 Project Management:**
- Milestone documentation and reporting
- Technical decision documentation
- Risk assessment documentation
- Change impact analysis documentation
- Project status reporting
- Stakeholder communication documents

### **Process Violation Prevention:**

**NEVER DO THESE without project-documentor:**
- ❌ Edit CLAUDE.md directly
- ❌ Update agent usage rules
- ❌ Modify change management processes  
- ❌ Change documentation templates
- ❌ Update project governance rules
- ❌ Modify development processes
- ❌ Create formal project documentation
- ❌ Document scope or timeline changes

**ALWAYS DO THESE:**
- ✅ Call project-documentor FIRST for ANY governance change
- ✅ Call project-documentor FIRST for ANY documentation creation
- ✅ Create proper change documentation through project-documentor
- ✅ Follow project-documentor's documentation strategy
- ✅ Validate process compliance through project-documentor
- ✅ Use project-documentor for ALL project management documentation

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

#### **CODING AGENT MANDATORY WORKFLOW:**

**ALL coding subagents (mcp-server-architect, storage-engineer, tools-developer, search-engineer, testing-specialist) MUST follow these mandatory documentation review requirements:**

```
BEFORE Starting ANY Coding Task:
1. ✅ Read DEVELOPMENT_STATUS.md (existing requirement - for current context)
2. ✅ Read TECHNICAL_ARCHITECTURE.md (focus on relevant sections for your component)
3. ✅ Read SYSTEM_DESIGN_REQUIREMENTS.md (focus on architectural constraints)

AFTER Completing ANY Coding Task:
1. ✅ Validate implementation against architectural requirements
2. ✅ Check component integration specifications match your implementation  
3. ✅ Document any architectural deviations in development status updates
4. ✅ Confirm your implementation supports clean interfaces with other agents
```

**Rationale**: This mandatory workflow prevents architectural conflicts and integration issues that could require hours of rework. The 5-10 minute documentation review saves significant development time and ensures system consistency.

**Enforcement**: Any coding agent that skips these requirements risks creating integration conflicts, architectural violations, or rework cycles that impact the 3-day timeline.

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
1. ✅ **BEFORE updating DEVELOPMENT_STATUS.md:**
   - **ALWAYS check actual local time using**: `date "+%Y-%m-%d %H:%M"` 
   - **Use actual system timestamp** in "Updated" column
   - **NEVER use estimated or future timestamps**
2. ✅ **IMMEDIATELY** update `docs/project-management/DEVELOPMENT_STATUS.md`:
   - Change task status from ⏳ PENDING to ✅ COMPLETE
   - Add completion timestamp (from step 1)
   - Add any notes about issues or discoveries
   - Update progress metrics
3. ✅ Update "Current Development Context" section with what you just completed
4. ✅ Update "Immediate Next Steps" with next task to work on

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
✅ MANDATORY: Any changes to CLAUDE.md governance rules
✅ MANDATORY: Any changes to process documentation
✅ MANDATORY: Any changes to agent usage guidelines
✅ MANDATORY: Any changes to project management processes
✅ MANDATORY: Any changes to documentation templates or standards

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

## 🎯 **SUBAGENT GOVERNANCE BRIEFING PROTOCOL**

### **CRITICAL REQUIREMENT: ALL Subagent Calls Must Include Governance Briefing**

**MANDATORY**: Every Claude Code call to any subagent (mcp-server-architect, storage-engineer, tools-developer, search-engineer, testing-specialist, project-coordinator, project-documentor, or any agent) MUST include comprehensive governance briefing to ensure project management protocol compliance.

**NO EXCEPTIONS**: This requirement applies to ALL agent interactions without exception.

---

### **STANDARD SUBAGENT GOVERNANCE BRIEFING TEMPLATE**

**When calling ANY subagent, Claude Code MUST provide this standard briefing:**

```
**🎯 GOVERNANCE BRIEFING FOR [AGENT_TYPE] - mydocs-mcp Project**

**PROJECT CONTEXT**:
- **Project**: mydocs-mcp Personal Document Intelligence MCP Server  
- **Timeline**: 3-day MVP sprint (72 hours total) - NO EXTENSIONS ALLOWED
- **Current Status**: [Current development phase, day, and specific task]
- **Sprint Phase**: [Pre-development/Day 1/Day 2/Day 3] - [Hours remaining]
- **Scope**: MVP ONLY - NO feature expansion beyond documented scope

**🚨 MANDATORY READING** (Read these documents FIRST before proceeding):
1. **docs/project-management/DEVELOPMENT_STATUS.md** - Current progress, immediate priorities, session context
2. **docs/TECHNICAL_ARCHITECTURE.md** - Technical constraints, decisions, architecture requirements  
3. **docs/SYSTEM_DESIGN_REQUIREMENTS.md** - System design requirements and performance specifications
4. **docs/project-management/PROJECT_SCOPE_3DAY.md** - IMMUTABLE scope boundaries (IN/OUT OF SCOPE)
5. **docs/project-management/CHANGES_INDEX.md** - Recent changes and current project modifications

**📋 PROCESS COMPLIANCE REQUIREMENTS** (MANDATORY - NO EXCEPTIONS):
1. **Follow ALL protocols in CLAUDE.md** without exception or modification
2. **Document changes immediately** using individual change files for medium/high impact or CHANGES_INDEX.md for low impact
3. **Update DEVELOPMENT_STATUS.md** after completing ANY task (change status from PENDING to COMPLETE)
4. **Verify scope compliance** before implementing ANY change - check PROJECT_SCOPE_3DAY.md
5. **NO timeline extensions** - work strictly within 72-hour constraint  
6. **Maintain performance requirements** - sub-200ms response times for all operations
7. **Follow MCP protocol compliance** standards without compromise
8. **Update session handoff notes** in DEVELOPMENT_STATUS.md before completing work

**🛡️ SCOPE PROTECTION** (CRITICAL - Violation will stop project):
- **ONLY implement features** listed in IN SCOPE section of PROJECT_SCOPE_3DAY.md
- **NEVER add OUT OF SCOPE features** without formal change request approval process
- **NEVER extend 3-day timeline** under any circumstances
- **Focus on MVP delivery ONLY** - no feature expansion or optimization beyond requirements
- **Question anything** that seems to expand scope and STOP if unsure

**📦 DELIVERABLE HANDOFF REQUIREMENTS** (Complete before finishing work):
1. **Update task status** in DEVELOPMENT_STATUS.md immediately after completion (PENDING → COMPLETE)
2. **Log significant changes** in change management system using appropriate change file or index
3. **Ensure code/documentation standards** match project requirements and architecture decisions
4. **Verify integration** with existing components and maintain compatibility  
5. **Test performance requirements** - validate sub-200ms targets are met
6. **Update immediate priorities** in DEVELOPMENT_STATUS.md for next session continuity
7. **Document any blockers** or issues encountered for next session awareness
8. **Verify deliverable quality** meets MVP standards and project requirements

**🔍 QUALITY ASSURANCE CHECKLIST** (Verify before completion):
- [ ] All changes align with TECHNICAL_ARCHITECTURE.md decisions
- [ ] Performance requirements met (sub-200ms targets)  
- [ ] MCP protocol compliance maintained
- [ ] Documentation updated to reflect actual implementation
- [ ] Integration testing completed for affected components
- [ ] No scope violations introduced
- [ ] Timeline impact assessed and documented
- [ ] Session handoff information prepared

**[AGENT_SPECIFIC_PROTOCOLS]** - See specialized requirements below for your agent type
```

---

### **AGENT-SPECIFIC PROTOCOL EXTENSIONS**

#### **For mcp-server-architect Agent**:
```
**SPECIALIZED REQUIREMENTS - MCP Server Architecture**:
- **MCP Protocol Focus**: Ensure strict MCP protocol compliance - no protocol deviations
- **Transport Layer**: Use stdio transport only (no HTTP+SSE as it's OUT OF SCOPE)
- **Tool Registry**: Implement comprehensive tool registry with async execution support
- **Server Lifecycle**: Follow MCP server lifecycle management standards  
- **Performance**: Target sub-200ms tool response times
- **Architecture**: Follow docs/TECHNICAL_ARCHITECTURE.md decisions exactly
- **Integration**: Ensure clean interfaces for storage, tools, and search components
- **Documentation**: Update technical documentation to match actual server implementation
```

#### **For storage-engineer Agent**:
```
**SPECIALIZED REQUIREMENTS - Database and Storage**:
- **SQLite Focus**: Use SQLite only - no other database systems (PostgreSQL is OUT OF SCOPE)
- **Performance Target**: Sub-200ms query response times (P95 performance requirement)
- **Schema Design**: Follow TECHNICAL_ARCHITECTURE.md database schema specifications
- **Async Support**: Implement async database operations with connection pooling
- **Data Integrity**: Ensure ACID compliance and data consistency
- **Migration System**: Implement schema versioning and migration support
- **Query Optimization**: Focus on search index optimization for fast document retrieval
- **Documentation**: Update database documentation with actual schema and performance metrics
```

#### **For tools-developer Agent**:
```
**SPECIALIZED REQUIREMENTS - MCP Tools Implementation**:
- **Tool Interface**: Implement exactly 3 MCP tools - indexDocument, searchDocuments, getDocument
- **Parameter Validation**: Strict input validation and error handling for all tools
- **MCP Compliance**: Follow MCP protocol tool interface specifications exactly
- **Performance**: Each tool must respond within sub-200ms requirement
- **Error Handling**: Comprehensive error responses with proper MCP error format
- **Integration**: Clean integration with storage and search engine components
- **Documentation**: Create comprehensive API documentation for each tool
- **Testing**: Unit testing for each tool with performance validation
```

#### **For search-engineer Agent**:
```
**SPECIALIZED REQUIREMENTS - Search Engine Development**:
- **Search Type**: Keyword search ONLY - no semantic search (OUT OF SCOPE)
- **Performance**: Sub-200ms search response time requirement
- **Relevance**: Basic relevance scoring based on keyword matching and document metadata  
- **Result Format**: JSON response format matching MCP tool specifications
- **Index Optimization**: Focus on search index performance for fast document retrieval
- **Query Processing**: Efficient query parsing and processing algorithms
- **Integration**: Clean interface with storage layer for search index management
- **Documentation**: Document search algorithms and performance characteristics
```

#### **For testing-specialist Agent**:
```
**SPECIALIZED REQUIREMENTS - Testing and Quality Assurance**:
- **Test Coverage**: Target >95% code coverage across all components
- **Performance Testing**: Validate sub-200ms response time requirements
- **Integration Testing**: End-to-end MCP protocol testing with Claude Code
- **Unit Testing**: Comprehensive unit tests for all components and tools
- **Test Automation**: Automated test execution and reporting
- **Quality Metrics**: Track and report quality metrics throughout development
- **Bug Tracking**: Document and track any issues discovered during testing
- **Documentation**: Create testing documentation and quality reports
```

---

### **GOVERNANCE BRIEFING ENFORCEMENT**

#### **MANDATORY COMPLIANCE VERIFICATION**:
1. **Before Starting Work**: Agent MUST confirm reading all mandatory documents
2. **During Work**: Agent MUST verify scope compliance for each implementation decision  
3. **After Completing Work**: Agent MUST complete all deliverable handoff requirements
4. **Session Handoff**: Agent MUST update DEVELOPMENT_STATUS.md with current state

#### **COMPLIANCE VERIFICATION CHECKLIST** (For Claude Code):
- [ ] **Governance briefing provided** to subagent with all required sections
- [ ] **Agent-specific protocols** included for the specific agent type
- [ ] **Mandatory documents** confirmed as read by subagent
- [ ] **Scope compliance** verified during subagent work  
- [ ] **Deliverable handoff** completed by subagent before session end
- [ ] **Documentation updates** completed per requirements
- [ ] **DEVELOPMENT_STATUS.md** updated with task completion and next priorities

#### **ESCALATION FOR NON-COMPLIANCE**:
```
IF subagent fails to follow governance briefing requirements:
1. STOP current work immediately
2. Re-brief agent on missed requirements
3. Verify compliance before proceeding
4. Document compliance issue in CHANGES_INDEX.md
5. If repeated non-compliance, escalate to human review
```

---

### **SUBAGENT HANDOFF PROTOCOL SUMMARY**

#### **BEFORE Calling Subagent** (Claude Code Requirements):
1. ✅ **Prepare governance briefing** using standard template
2. ✅ **Add agent-specific protocols** for the called agent type
3. ✅ **Include current project status** and immediate task context
4. ✅ **Provide all required document references** for mandatory reading
5. ✅ **Set clear deliverable expectations** and handoff requirements

#### **DURING Subagent Work** (Monitoring Requirements):
1. ✅ **Verify document reading** compliance by subagent
2. ✅ **Monitor scope compliance** throughout agent work
3. ✅ **Ensure process adherence** to CLAUDE.md protocols
4. ✅ **Track deliverable progress** against requirements
5. ✅ **Validate quality standards** during implementation

#### **AFTER Subagent Completion** (Handoff Verification):
1. ✅ **Confirm deliverable completion** meets all requirements  
2. ✅ **Verify DEVELOPMENT_STATUS.md updates** completed correctly
3. ✅ **Check documentation updates** reflect actual implementation
4. ✅ **Validate performance requirements** met (sub-200ms targets)
5. ✅ **Ensure session continuity** with proper handoff notes
6. ✅ **Update change management** with appropriate change documentation

---

**CRITICAL SUCCESS FACTOR**: This subagent governance briefing protocol is ESSENTIAL for maintaining project integrity, timeline adherence, and scope compliance throughout the mydocs-mcp 3-day development sprint. ALL subagent interactions MUST follow this protocol without exception.

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

**Document Version**: 1.1 (Added Subagent Governance Briefing Protocol)  
**Last Updated**: September 4, 2025  
**For**: mydocs-mcp 3-day development sprint