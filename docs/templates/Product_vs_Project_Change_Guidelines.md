# Product vs Project Change Management Guidelines

## 🎯 **When to Use Each Template**

### **Use PCR Template (Product Change Request) for STRATEGIC changes:**

#### **Product Features & Capabilities**
- Adding new core features to mydocs-mcp
- Changing existing feature behavior that affects user experience
- Removing or deprecating features
- Modifying feature specifications or requirements

#### **User Experience Changes**
- Changes to user interface or interaction patterns
- Modifications to user journey or workflow
- Adjustments to user onboarding or setup process
- Changes affecting user satisfaction or adoption

#### **Strategic Direction**
- Product vision or mission changes
- Market positioning adjustments
- Target user persona modifications
- Competitive strategy changes

#### **Roadmap & Planning**
- Major milestone adjustments
- Feature prioritization changes
- Product backlog reordering
- Long-term product evolution decisions

---

### **Use CHANGE Template (Technical Change Request) for TACTICAL changes:**

#### **Implementation Details**
- Code structure and architecture decisions
- Technology stack choices
- Database schema changes
- API design modifications

#### **Development Process**
- Build and deployment process changes
- Testing strategy modifications
- Code review process updates
- Development tool changes

#### **Project Execution**
- Timeline adjustments within current scope
- Resource allocation changes
- Task breakdown modifications
- Sprint planning adjustments

#### **Quality & Performance**
- Performance optimization approaches
- Bug fix implementations
- Security improvement measures
- Code quality standard updates

---

## 🔄 **Change Flow Process**

### **Product Change Flow (PCR)**
1. **Strategic Assessment**: Evaluate product impact and alignment
2. **PCR Creation**: Use PCR template for comprehensive documentation
3. **Stakeholder Review**: Product owner, business stakeholders review
4. **Approval Process**: Strategic approval for product direction
5. **Implementation Planning**: Break down into project-level changes
6. **Project Execution**: Create CHANGE-XXX files for implementation
7. **Success Monitoring**: Track product metrics and user impact

### **Project Change Flow (CHANGE)**
1. **Technical Assessment**: Evaluate implementation impact
2. **CHANGE Creation**: Use CHANGE template for detailed documentation
3. **Technical Review**: Technical lead and team review
4. **Implementation**: Direct implementation or quick approval
5. **Validation**: Testing and quality assurance
6. **Documentation Update**: Update technical documentation
7. **Completion Tracking**: Mark complete with metrics

---

## 📊 **Decision Matrix**

| Question | PCR (Product) | CHANGE (Project) |
|----------|---------------|------------------|
| Does this affect what the product does? | ✅ Yes | ❌ No |
| Does this change user experience? | ✅ Yes | ❌ No |
| Does this require business approval? | ✅ Yes | ❌ Usually No |
| Is this about HOW we build it? | ❌ No | ✅ Yes |
| Does this affect competitive position? | ✅ Yes | ❌ No |
| Is this a technical implementation choice? | ❌ No | ✅ Yes |
| Does this impact product roadmap? | ✅ Yes | ❌ No |
| Is this about development process? | ❌ No | ✅ Yes |

---

## 💡 **Examples by Category**

### **PCR Examples (Product Changes)**
- **PCR-001**: Add semantic search capability to mydocs-mcp
- **PCR-002**: Implement multi-language document support
- **PCR-003**: Create document template generation feature
- **PCR-004**: Add collaboration features for shared documents
- **PCR-005**: Implement advanced analytics dashboard

### **CHANGE Examples (Project Changes)**
- **CHANGE-015**: Optimize SQLite query performance for search
- **CHANGE-016**: Implement connection pooling for MCP server
- **CHANGE-017**: Add comprehensive error logging system
- **CHANGE-018**: Upgrade Python dependencies to latest versions
- **CHANGE-019**: Refactor indexing pipeline for better maintainability

---

## 🚨 **Common Mistakes to Avoid**

### **Don't Use PCR For:**
- ❌ Code refactoring that doesn't change functionality
- ❌ Bug fixes that restore intended behavior
- ❌ Performance optimizations with same user experience
- ❌ Development tooling changes
- ❌ Testing strategy improvements

### **Don't Use CHANGE For:**
- ❌ Adding new features users will interact with
- ❌ Changing what the product is capable of doing
- ❌ Modifying user-facing behavior or interface
- ❌ Strategic direction or vision changes
- ❌ Market positioning adjustments

---

## 🔗 **Integration Between PCR and CHANGE**

### **PCR → CHANGE Flow**
1. **PCR Approved**: Strategic product change approved
2. **Implementation Planning**: Break down into technical tasks
3. **CHANGE Creation**: Create multiple CHANGE files for implementation
4. **Cross-Reference**: Link CHANGE files back to originating PCR
5. **Coordinated Delivery**: Ensure all CHANGE items deliver PCR goals

### **CHANGE Impact on PCR**
- Major technical constraints may require PCR updates
- Implementation discoveries may affect product requirements
- Performance implications may influence product specifications
- Technical feasibility issues may require PCR scope adjustments

---

## 📁 **File Organization**

### **PCR Files Location**
```
docs/
├── product-management/
│   ├── product-changes/
│   │   ├── PCR-001-semantic-search-capability.md
│   │   ├── PCR-002-multi-language-support.md
│   │   └── PCR-XXX-[description].md
│   └── Product_Change_Log.md
```

### **CHANGE Files Location**
```
docs/
├── project-management/
│   ├── changes/
│   │   ├── CHANGE-001-day2-system-validation.md
│   │   ├── CHANGE-002-change-management-restructure.md
│   │   └── CHANGE-XXX-[description].md
│   └── Change_Control_Log.md
```

---

## 📝 **Template Selection Quick Reference**

### **Use PCR Template When:**
- Change affects WHAT the product does
- Change impacts user experience or value
- Change requires strategic/business approval
- Change affects product positioning or roadmap

### **Use CHANGE Template When:**
- Change affects HOW we build the product
- Change is about implementation or development process
- Change is tactical or technical in nature
- Change can be approved by technical team

### **Still Not Sure?**
1. Ask: "Would a user notice this change?"
   - Yes → Probably PCR
   - No → Probably CHANGE

2. Ask: "Does this change what we're building or how we're building it?"
   - What → PCR
   - How → CHANGE

3. Ask: "Who needs to approve this?"
   - Business stakeholders → PCR
   - Technical team → CHANGE

---

**Remember**: When in doubt, start with the impact assessment. If the change affects user experience, product capabilities, or strategic direction, use PCR. If it's about implementation, process, or technical approach, use CHANGE.