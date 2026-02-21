/**
 * Email MCP Server - Test Script
 * ===============================
 * Test draft and send functionality
 */

const fs = require('fs');
const path = require('path');

const PROJECT_ROOT = path.resolve(__dirname, '..');
const PLANS_DIR = path.join(PROJECT_ROOT, 'Plans');
const PENDING_APPROVAL_DIR = path.join(PROJECT_ROOT, 'Pending_Approval');
const APPROVED_DIR = path.join(PROJECT_ROOT, 'Approved');

console.log('='.repeat(60));
console.log('Email MCP Server - Test Script');
console.log('='.repeat(60));
console.log();

// Test 1: Create a draft
console.log('TEST 1: Create Email Draft');
console.log('-'.repeat(40));

const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, -5);
const draftFilename = `email_draft_${timestamp}.md`;
const draftFilepath = path.join(PLANS_DIR, draftFilename);

const draftContent = `---
type: email_draft
to: test@example.com
subject: Test Email from MCP Server
created: ${new Date().toISOString()}
status: draft
---

# Email Draft

## Recipients
- **To:** test@example.com

## Subject
Test Email from MCP Server

## Body

This is a test email created by the Email MCP Server.

---
*Status: draft - Requires HITL approval*
`;

try {
  fs.writeFileSync(draftFilepath, draftContent, 'utf-8');
  console.log(`✓ Draft created: ${draftFilename}`);
  console.log(`  Location: ${draftFilepath}`);
} catch (error) {
  console.log(`✗ Error creating draft: ${error.message}`);
}

console.log();

// Test 2: List drafts
console.log('TEST 2: List Email Drafts');
console.log('-'.repeat(40));

try {
  const files = fs.readdirSync(PLANS_DIR);
  const drafts = files.filter(f => f.startsWith('email_draft_') && f.endsWith('.md'));
  console.log(`Found ${drafts.length} draft(s):`);
  drafts.forEach(d => console.log(`  - ${d}`));
} catch (error) {
  console.log(`✗ Error listing drafts: ${error.message}`);
}

console.log();

// Test 3: Simulate approval workflow
console.log('TEST 3: Approval Workflow');
console.log('-'.repeat(40));

const approvedFilepath = path.join(APPROVED_DIR, draftFilename);
try {
  fs.copyFileSync(draftFilepath, approvedFilepath);
  console.log(`✓ Draft approved (copied to /Approved/)`);
  console.log(`  Location: ${approvedFilepath}`);
} catch (error) {
  console.log(`✗ Error approving draft: ${error.message}`);
}

console.log();
console.log('='.repeat(60));
console.log('Test Summary');
console.log('='.repeat(60));
console.log();
console.log('Files created:');
console.log(`  1. ${draftFilepath}`);
console.log(`  2. ${approvedFilepath}`);
console.log();
console.log('Next steps:');
console.log('  1. Set up credentials.json from Google Cloud Console');
console.log('  2. Run: node mcp_servers/email-mcp/index.js');
console.log('  3. Use MCP client to call draft_email and send_email tools');
console.log();
