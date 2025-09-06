# CLAUDE.md - AI Agent Documentation Management Rules
## mydocs-mcp Project

## PRIMARY DIRECTIVE
**Claude Code MUST follow these rules for project consistency and 3-day timeline delivery.**

## TABLE OF CONTENTS
1. [User Request Validation](#user-request-validation)
2. [Pre-Task Document Review](#pre-task-document-review)
3. [project-documentor Usage](#project-documentor-usage)
4. [Documentation Hierarchy](#documentation-hierarchy)
5. [Agent Integration](#agent-integration)
6. [Change Management](#change-management)
7. [Critical Restrictions](#critical-restrictions)
8. [Subagent Governance](#subagent-governance)

## USER REQUEST VALIDATION

### CRITICAL: ALL User Requests Must Be Analyzed FIRST
**BEFORE implementing ANY request, IMMEDIATELY call project-coordinator agent (NO EXCEPTIONS)**

**Provide project-coordinator:**
- Exact user request (verbatim)
- Current project context and status
- Technical implications and potential conflicts
- Impact on scope, timeline, or architecture

**Based on response:**
- APPROVED → Proceed with implementation
- CONCERNS → Discuss with user before proceeding
- REJECTED → Explain why and offer alternatives
- UNCLEAR → Ask user for clarification

**Examples requiring validation:**
- File location changes ("put test file in root")
- Technical approach changes ("skip database, use JSON")
- Feature additions ("quickly add this feature")

**NO BLIND AGREEMENT Policy:**
- ❌ NEVER automatically agree with user suggestions
- ❌ NEVER skip validation to save time
- ✅ ALWAYS validate through project-coordinator
- ✅ ALWAYS protect project integrity

## PRE-TASK DOCUMENT REVIEW

### CRITICAL: Mandatory Document Review Before Each Development Task
**ALL development tasks MUST begin with this protocol (NO EXCEPTIONS)**

### MANDATORY DOCUMENTS (15-30 seconds per task)
**BEFORE starting ANY development task:**

1. **Project_Status_Report.md** - Current context, priorities, session continuity
2. **Technical_Design_Document.md** - Technical constraints, performance (sub-200ms)
3. **Work_Breakdown_Structure.md** - Code structure, file organization
4. **System_Requirements_Specification.md** - Design constraints, quality requirements

### Quick Validation Checklist
- [ ] Current context verified
- [ ] Technical approach confirmed
- [ ] Performance targets known (sub-200ms)
- [ ] Integration constraints checked
- [ ] Scope compliance verified

### Specialized Extensions
**Architecture Tasks**: Review System_Requirements_Specification.md in detail
**Database Tasks**: Check schema specs, query performance targets
**MCP Tasks**: Verify protocol compliance, stdio transport only

### Enforcement
- Every task MUST begin with document review
- No development without protocol completion
- Update Project_Status_Report.md after task completion
- If protocol skipped: STOP work, complete protocol, verify alignment

## project-documentor USAGE

### CRITICAL: Call project-documentor for ANY documentation governance changes

### GOVERNANCE DOCUMENTS (ALWAYS use project-documentor)
- CLAUDE.md (this file)
- Project_Charter.md
- Change_Control_Log.md
- Project_Status_Report.md
- docs/project-management/* files
- docs/templates/* files

### PROCESS DOCUMENTS (ALWAYS use project-documentor)
- Agent usage guidelines
- Workflow documentation
- Change management processes
- Quality assurance processes

### Usage Protocol
**WHEN changing governance/process documents:**
1. STOP implementation immediately
2. Call project-documentor FIRST
3. Provide full context
4. Follow project-documentor's guidance
5. Create proper change documentation
6. ONLY THEN proceed with implementation

### Explicit Triggers
**IMMEDIATE project-documentor REQUIRED for:**
- ANY edit to CLAUDE.md
- Creating project management documents
- Technical specifications updates
- Milestone summaries
- Agent integration documentation
- Process or workflow changes
- Scope/timeline documentation changes

### Process Violations
**NEVER without project-documentor:**
- ❌ Edit CLAUDE.md directly
- ❌ Update agent usage rules
- ❌ Modify change management processes
- ❌ Create formal project documentation

**ALWAYS:**
- ✅ Call project-documentor FIRST for governance changes
- ✅ Follow project-documentor's strategy
- ✅ Use project-documentor for ALL project management docs

## DOCUMENTATION HIERARCHY

### IMMUTABLE DOCUMENTS (Cannot change without formal approval)
- Project_Charter.md - The project contract
- Core deliverables and timeline
- Success criteria and metrics
- IN SCOPE vs OUT OF SCOPE boundaries

### UPDATEABLE DOCUMENTS (Can modify with tracking)
- Work_Breakdown_Structure.md - Implementation details
- PersonalDocAgent_MCP_PRD.md - Technical specifications
- README.md - Usage instructions
- API documentation - Technical references

## AGENT INTEGRATION

### Available Agents

**Project Management:**
- **project-coordinator**: Implementation validation, technical decisions, user intent clarification
- **project-documentor**: Project docs, requirements, specifications, process documentation
- **draw.io MCP**: System diagrams, architecture visualization, flowcharts

**Development Specialists:**
- **mcp-server-architect**: MCP server core, protocol compliance, transport implementation
- **storage-engineer**: Database design, SQLite optimization, data modeling
- **tools-developer**: MCP tools (searchDocuments, getDocument, indexDocument)
- **search-engineer**: Search algorithms, query processing, relevance scoring
- **testing-specialist**: Testing, performance validation, quality assurance

### Usage Guidelines

**Project Management Workflow:**
- Use project-coordinator when implementation unclear/disputed
- Use project-documentor for comprehensive documentation tasks
- Use draw.io MCP for visual documentation (save in docs/diagrams/)

**Development Dependencies:**
1. mcp-server-architect (foundation)
2. storage-engineer (required for tools/search)
3. tools-developer + search-engineer (parallel)
4. testing-specialist (validates all)

### Coding Agent Mandatory Workflow
**ALL coding agents MUST:**

**BEFORE Starting:**
- Read Project_Status_Report.md
- Read Technical_Design_Document.md
- Read System_Requirements_Specification.md

**AFTER Completing:**
- Validate against architectural requirements
- Check integration specifications
- Document deviations
- Confirm clean interfaces

## CHANGE MANAGEMENT

### Core Rules

**Rule 1: Check Scope First**
BEFORE ANY change:
1. Read Project_Charter.md
2. Verify alignment with IN SCOPE items
3. If affects OUT OF SCOPE → STOP and request approval

**Rule 2: Document Changes**
- **Medium/High Impact**: Create individual change file + update Change_Control_Log.md
- **Low Impact**: Log directly in Change_Control_Log.md

**Rule 3: Scope Changes Need Approval**
IF affects timeline/deliverables/success criteria:
1. Create change request using template
2. Create change file with "PENDING APPROVAL"
3. Do NOT implement until approved

### Change Impact Levels

**LOW (Code Implementation)**
- Examples: Variable names, function structure
- Actions: Implement freely, update comments, log in git

**MEDIUM (Technical Approach)**
- Examples: Database choice, library selection
- Actions: Update Work_Breakdown_Structure.md, log in Change_Control_Log.md

**HIGH (Scope/Timeline)**
- Examples: Adding features, extending deadline
- Actions: STOP, create change request, wait for approval

## DOCUMENTATION UPDATES

### CRITICAL: Read Project_Status_Report.md First
**EVERY session MUST start by reading Project_Status_Report.md**
- Source of truth for current progress
- Tells you what to work on next
- Provides complete session continuity

### Session Workflow

**Session Start:**
1. Read Project_Status_Report.md
2. Update "Current Development Context"
3. Use project-documentor for documentation tasks
4. Use draw.io MCP for diagrams

**After Each Task (MANDATORY):**
1. Check actual time: `date "+%Y-%m-%d %H:%M"`
2. Update Project_Status_Report.md:
   - Change status: PENDING → COMPLETE
   - Add timestamp and notes
   - Update progress metrics
3. Update "Current Development Context"
4. Update "Immediate Next Steps"

**Session End (CRITICAL):**
- Update Project_Status_Report.md "Session Handoff Notes"
- Document current state and next priority
- Note any blockers or issues

### Document Update Categories

**IMMUTABLE (Never update without approval):**
- Project_Charter.md
- Core deliverables and timeline
- IN/OUT OF SCOPE boundaries

**REAL-TIME (Update constantly):**
- Project_Status_Report.md (after every task)
- Change_Control_Log.md (with all changes)

**REGULAR (Update as progresses):**
- Work_Breakdown_Structure.md
- Technical_Design_Document.md
- API documentation

### Update Frequency
- **Every task**: Project_Status_Report.md (MANDATORY)
- **4-hour blocks**: Detailed progress updates
- **Daily milestones**: Change_Control_Log.md summary
- **Session end**: Handoff notes (MANDATORY)

### Validation Checklist
**Before ANY change:**
- [ ] Listed in IN SCOPE
- [ ] Doesn't affect OUT OF SCOPE
- [ ] Doesn't extend 3-day timeline
- [ ] Supports success criteria
- [ ] Identify documentation impact
- [ ] Verify MCP protocol compliance

## CRITICAL RESTRICTIONS

### NEVER WITHOUT APPROVAL
- ❌ Change 3-day timeline
- ❌ Add OUT OF SCOPE features
- ❌ Remove IN SCOPE features
- ❌ Change core MCP tool specs
- ❌ Modify success criteria

### ALWAYS DO
- ✅ Check scope before implementing
- ✅ Create change files for medium+ impact
- ✅ Keep documentation current
- ✅ Verify MCP protocol compliance
- ✅ Focus on 3-day delivery

### Change Request Process
1. **Identify**: If affects scope/timeline/deliverables → Create CHANGE_REQUEST_XXX.md → STOP
2. **Document**: Use template
3. **Wait**: No implementation without approval
4. **Implement**: If approved → Update docs → Proceed

### Success Metrics
- ✅ Zero scope violations
- ✅ Complete change tracking
- ✅ Documentation consistency
- ✅ Timeline adherence
- ✅ Approval compliance

### Escalation Scenarios
**STOP and Ask for Help:**
- Change extends timeline beyond 3 days
- Change requires OUT OF SCOPE features
- Technical blocker prevents completion

**Proceed Freely:**
- Code refactoring
- Documentation improvements
- Bug fixes within scope

## SUBAGENT GOVERNANCE

### CRITICAL: ALL Subagent Calls Must Include Governance Briefing
**MANDATORY for all agent interactions (NO EXCEPTIONS)**

### Standard Briefing Template
**When calling ANY subagent, provide:**

```
GOVERNANCE BRIEFING FOR [AGENT_TYPE] - mydocs-mcp Project

PROJECT CONTEXT:
- 3-day MVP sprint (72 hours total) - NO EXTENSIONS
- Current Status: [phase, day, specific task]
- Scope: MVP ONLY - NO feature expansion

MANDATORY READING (Read FIRST):
1. Project_Status_Report.md - Progress, priorities, context
2. Technical_Design_Document.md - Technical constraints, sub-200ms targets
3. System_Requirements_Specification.md - Design requirements
4. Project_Charter.md - IMMUTABLE scope boundaries
5. Change_Control_Log.md - Recent changes

COMPLIANCE REQUIREMENTS:
- Follow ALL CLAUDE.md protocols
- Document changes immediately
- Update Project_Status_Report.md after tasks
- Verify scope compliance before changes
- NO timeline extensions (72-hour constraint)
- Maintain sub-200ms performance
- Update session handoff notes

SCOPE PROTECTION:
- ONLY implement IN SCOPE features
- NEVER add OUT OF SCOPE without approval
- Focus on MVP delivery ONLY
- Question scope expansions and STOP if unsure

DELIVERABLE HANDOFF:
- Update task status (PENDING → COMPLETE)
- Log significant changes
- Verify integration compatibility
- Test performance targets
- Document blockers/issues
```

### Agent-Specific Requirements

**mcp-server-architect**: MCP protocol compliance, stdio transport only, tool registry, sub-200ms responses
**storage-engineer**: SQLite only, sub-200ms queries, schema design, async operations
**tools-developer**: 3 MCP tools (indexDocument, searchDocuments, getDocument), validation, error handling
**search-engineer**: Keyword search only, sub-200ms responses, relevance scoring
**testing-specialist**: >95% coverage, performance testing, integration testing

### Compliance Verification
**Before/During/After each subagent call:**
- [ ] Governance briefing provided
- [ ] Agent-specific protocols included
- [ ] Mandatory documents confirmed read
- [ ] Scope compliance verified
- [ ] Deliverable handoff completed
- [ ] Project_Status_Report.md updated

---

## QUICK REFERENCE

### Critical Workflow
1. **User Request** → Call project-coordinator FIRST (NO EXCEPTIONS)
2. **Development Task** → Read mandatory documents (15-30s)
3. **Documentation Changes** → Call project-documentor FIRST
4. **After Each Task** → Update Project_Status_Report.md (MANDATORY)
5. **Subagent Calls** → Include governance briefing (MANDATORY)

### Key Documents
- **Project_Status_Report.md** - Start every session here
- **Project_Charter.md** - IMMUTABLE boundaries
- **Technical_Design_Document.md** - Technical constraints
- **Change_Control_Log.md** - Track all changes

### Performance Targets
- Sub-200ms response times (ALL operations)
- >95% test coverage
- 72-hour timeline (NO EXTENSIONS)

### Scope Protection
- IN SCOPE → Implement freely
- OUT OF SCOPE → STOP, request approval
- Timeline impact → Create change request

**Remember: When in doubt, ASK FOR CLARIFICATION rather than assume.**

---

**Document Version**: 1.2 (Optimized - 70% size reduction)  
**Last Updated**: September 5, 2025  
**For**: mydocs-mcp 3-day development sprint