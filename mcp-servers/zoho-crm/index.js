const { Server } = require("@modelcontextprotocol/sdk/server/index.js");
const { StdioServerTransport } = require("@modelcontextprotocol/sdk/server/stdio.js");

// Zoho CRM MCP Server for LIFE OS Company Layer
// Exposes Zoho CRM operations as MCP tools for Claude Code agents.

const ZOHO_BASE = "https://www.zohoapis.com.au/crm/v6";

let accessToken = null;
let tokenExpiry = 0;

async function refreshToken() {
  const res = await fetch("https://accounts.zoho.com.au/oauth/v2/token", {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: new URLSearchParams({
      grant_type: "refresh_token",
      client_id: process.env.ZOHO_CLIENT_ID,
      client_secret: process.env.ZOHO_CLIENT_SECRET,
      refresh_token: process.env.ZOHO_REFRESH_TOKEN,
    }),
  });
  const data = await res.json();
  accessToken = data.access_token;
  tokenExpiry = Date.now() + (data.expires_in - 60) * 1000;
  return accessToken;
}

async function getToken() {
  if (!accessToken || Date.now() >= tokenExpiry) {
    return refreshToken();
  }
  return accessToken;
}

async function zohoGet(path, params = {}) {
  const token = await getToken();
  const url = new URL(`${ZOHO_BASE}${path}`);
  Object.entries(params).forEach(([k, v]) => url.searchParams.set(k, v));
  const res = await fetch(url.toString(), {
    headers: { Authorization: `Zoho-oauthtoken ${token}` },
  });
  return res.json();
}

async function zohoPost(path, body) {
  const token = await getToken();
  const res = await fetch(`${ZOHO_BASE}${path}`, {
    method: "POST",
    headers: {
      Authorization: `Zoho-oauthtoken ${token}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify(body),
  });
  return res.json();
}

async function zohoPut(path, body) {
  const token = await getToken();
  const res = await fetch(`${ZOHO_BASE}${path}`, {
    method: "PUT",
    headers: {
      Authorization: `Zoho-oauthtoken ${token}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify(body),
  });
  return res.json();
}

const server = new Server(
  { name: "zoho-crm", version: "1.0.0" },
  { capabilities: { tools: {} } }
);

server.setRequestHandler("tools/list", async () => ({
  tools: [
    {
      name: "search_contacts",
      description: "Search Zoho CRM contacts by name, email, or company",
      inputSchema: {
        type: "object",
        properties: {
          criteria: { type: "string", description: "Search criteria (e.g. '(Email:equals:john@example.com)' or '(Last_Name:starts_with:Smith)')" },
          per_page: { type: "number", description: "Results per page (max 200)", default: 50 },
        },
        required: ["criteria"],
      },
    },
    {
      name: "get_contact",
      description: "Get a specific Zoho CRM contact by ID",
      inputSchema: {
        type: "object",
        properties: {
          id: { type: "string", description: "Zoho contact ID" },
        },
        required: ["id"],
      },
    },
    {
      name: "search_accounts",
      description: "Search Zoho CRM accounts by name or type",
      inputSchema: {
        type: "object",
        properties: {
          criteria: { type: "string", description: "Search criteria" },
          per_page: { type: "number", default: 50 },
        },
        required: ["criteria"],
      },
    },
    {
      name: "get_account",
      description: "Get a specific Zoho CRM account by ID",
      inputSchema: {
        type: "object",
        properties: {
          id: { type: "string", description: "Zoho account ID" },
        },
        required: ["id"],
      },
    },
    {
      name: "search_deals",
      description: "Search Zoho CRM deals by name, stage, or account",
      inputSchema: {
        type: "object",
        properties: {
          criteria: { type: "string", description: "Search criteria (e.g. '(Stage:equals:Negotiation)')" },
          per_page: { type: "number", default: 50 },
        },
        required: ["criteria"],
      },
    },
    {
      name: "get_deal",
      description: "Get a specific Zoho CRM deal by ID",
      inputSchema: {
        type: "object",
        properties: {
          id: { type: "string", description: "Zoho deal ID" },
        },
        required: ["id"],
      },
    },
    {
      name: "update_deal_stage",
      description: "Update the stage of a Zoho CRM deal. WRITE operation — requires explicit authorization.",
      inputSchema: {
        type: "object",
        properties: {
          id: { type: "string", description: "Zoho deal ID" },
          stage: { type: "string", description: "New stage value" },
        },
        required: ["id", "stage"],
      },
    },
    {
      name: "create_note",
      description: "Create a note on a Zoho CRM record. WRITE operation — requires explicit authorization.",
      inputSchema: {
        type: "object",
        properties: {
          parent_module: { type: "string", description: "Module: Contacts, Accounts, or Deals" },
          parent_id: { type: "string", description: "Record ID" },
          title: { type: "string", description: "Note title" },
          content: { type: "string", description: "Note content" },
        },
        required: ["parent_module", "parent_id", "title", "content"],
      },
    },
  ],
}));

server.setRequestHandler("tools/call", async (request) => {
  const { name, arguments: args } = request.params;

  switch (name) {
    case "search_contacts": {
      const data = await zohoGet("/Contacts/search", { criteria: args.criteria, per_page: args.per_page || 50 });
      return { content: [{ type: "text", text: JSON.stringify(data.data || [], null, 2) }] };
    }
    case "get_contact": {
      const data = await zohoGet(`/Contacts/${args.id}`);
      return { content: [{ type: "text", text: JSON.stringify(data.data?.[0] || {}, null, 2) }] };
    }
    case "search_accounts": {
      const data = await zohoGet("/Accounts/search", { criteria: args.criteria, per_page: args.per_page || 50 });
      return { content: [{ type: "text", text: JSON.stringify(data.data || [], null, 2) }] };
    }
    case "get_account": {
      const data = await zohoGet(`/Accounts/${args.id}`);
      return { content: [{ type: "text", text: JSON.stringify(data.data?.[0] || {}, null, 2) }] };
    }
    case "search_deals": {
      const data = await zohoGet("/Deals/search", { criteria: args.criteria, per_page: args.per_page || 50 });
      return { content: [{ type: "text", text: JSON.stringify(data.data || [], null, 2) }] };
    }
    case "get_deal": {
      const data = await zohoGet(`/Deals/${args.id}`);
      return { content: [{ type: "text", text: JSON.stringify(data.data?.[0] || {}, null, 2) }] };
    }
    case "update_deal_stage": {
      const data = await zohoPut(`/Deals/${args.id}`, { data: [{ Stage: args.stage }] });
      return { content: [{ type: "text", text: JSON.stringify(data, null, 2) }] };
    }
    case "create_note": {
      const data = await zohoPost(`/${args.parent_module}/${args.parent_id}/Notes`, {
        data: [{ Note_Title: args.title, Note_Content: args.content }],
      });
      return { content: [{ type: "text", text: JSON.stringify(data, null, 2) }] };
    }
    default:
      return { content: [{ type: "text", text: `Unknown tool: ${name}` }], isError: true };
  }
});

async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
}

main().catch(console.error);
