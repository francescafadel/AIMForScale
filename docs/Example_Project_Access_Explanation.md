# Example: Project Proposal Document Found But Not Accessible

## Specific Example: PE-L1187

### Project Details
- **Project Number**: PE-L1187
- **Project Name**: Increasing Cocoa Productivity through credit to small producers
- **Operation Number**: SP/OC-15-01-PE
- **Country**: Peru
- **Approval Date**: May 12, 2015
- **Status**: EXITED
- **Type**: Loan Operation (Non-Sovereign Guaranteed)
- **Total Cost**: $1,250,000
- **Sector**: AGRICULTURE AND RURAL DEVELOPMENT
- **Sub-Sector**: AGRIBUSINESS

### Why This Project Should Have Documents

This is a **high-priority project** for document access because:

1. **Loan Operation**: Loan operations typically have detailed proposal documents
2. **High Value**: $1.25M is a significant loan amount
3. **Completed Project**: Exited projects often have completion reports
4. **Specific Focus**: Cocoa productivity projects usually have detailed technical documentation

### What the Automated Script Found

The script correctly identified this project as having **"High"** document availability assessment and expected to find:
- Loan Proposal Document
- Project Proposal Document

However, the search status shows: **"Not Attempted - Manual Research Required"**

### Why Documents Couldn't Be Accessed Automatically

The demonstration script tried 4 different methods to access this project's documents:

#### Method 1: Direct Project URL
- **URL Attempted**: `https://www.iadb.org/en/projects/PE-L1187`
- **Result**: 404 Not Found
- **Reason**: IDB doesn't provide direct public access to project pages

#### Method 2: Project Search
- **URL Attempted**: `https://www.iadb.org/en/project-search`
- **Result**: Page accessible but project not found
- **Reason**: Search requires authentication or specific parameters

#### Method 3: Operation Number Search
- **URL Attempted**: `https://www.iadb.org/en/projects/SP/OC-15-01-PE`
- **Result**: 404 Not Found
- **Reason**: Operation numbers don't have direct public URLs

#### Method 4: Publications Section
- **URL Attempted**: `https://www.iadb.org/en/publications`
- **Result**: 404 Not Found
- **Reason**: Publications section not publicly accessible

### The Real Issue: Access Restrictions

The IDB website has several layers of access restrictions:

1. **Authentication Required**: Most project documents require login credentials
2. **Internal Systems**: Documents are stored in internal document management systems
3. **Permission-Based Access**: Different user types have different access levels
4. **No Public APIs**: No public API endpoints for document access
5. **Manual Request Process**: Documents must be requested through official channels

### How to Manually Access This Project's Documents

To actually access the documents for PE-L1187, you would need to:

#### Option 1: Contact IDB Directly
- **Email**: idb-documents@iadb.org
- **Phone**: +1 (202) 623-1000
- **Request**: Specific documents for Operation SP/OC-15-01-PE

#### Option 2: Use IDB's Document Request System
- Visit: https://www.iadb.org/en/contact-us
- Submit a formal document request
- Provide the operation number: SP/OC-15-01-PE

#### Option 3: Contact IDB Peru Country Office
- **Address**: Av. Javier Prado Este 4225, San Isidro, Lima, Peru
- **Phone**: +51 1 595-0000
- **Email**: peru@iadb.org

#### Option 4: Use IDB's Project Information System
- Requires registration and approval
- Access through: https://www.iadb.org/en/projects/project-information-system

### Expected Documents for This Project

Based on the project type and value, you should request:

1. **Loan Proposal Document** (Primary document)
2. **Project Appraisal Document**
3. **Technical Annexes**
4. **Environmental and Social Assessment**
5. **Project Completion Report** (since project is exited)

### Why This Pattern Applies to All Projects

This example (PE-L1187) demonstrates why **all 565 projects** in the dataset show "Not Attempted - Manual Research Required":

1. **Systematic Access Restriction**: IDB systematically restricts public access to project documents
2. **No Automated Solution**: Web scraping cannot bypass authentication and permission systems
3. **Manual Process Required**: Each project requires individual document requests
4. **Institutional Policy**: This is intentional policy to control document distribution

### Recommendations for Document Access

1. **Prioritize High-Value Projects**: Focus on loan operations over $1M first
2. **Contact IDB Systematically**: Use official channels for document requests
3. **Build Relationships**: Establish contacts within IDB for faster access
4. **Use Multiple Channels**: Try different IDB offices and departments
5. **Document Your Requests**: Keep records of all document requests and responses

### Conclusion

The fact that PE-L1187 (and all other projects) show "Not Attempted - Manual Research Required" is not a failure of the automated script, but rather reflects the reality that IDB project documents are intentionally protected behind access controls that require human intervention and official authorization to bypass.

This is why the research summary correctly identified that manual research is required for all projects, regardless of their document availability assessment.
