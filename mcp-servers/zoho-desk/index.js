const { Server } = require("@modelcontextprotocol/sdk/server/index.js");
const { StdioServerTransport } = require("@modelcontextprotocol/sdk/server/stdio.js");

// Zoho Desk MCP Server for LIFE OS Company Layer
// Exposes Zoho Desk ticket operations as MCP tools.

const ZOHO_DESK_BASE = "https://desk.zoho.com.au/api/v1";

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
  if (!accessToken || Date.now() >= tokenExpiry) return refreshToken();
  return accessToken;
}

async function deskGet(path, params = {}) {
  const token = await getToken();
  const url = new URL(`${ZOHO_DESK_BASE}${path}`);
  Object.entries(params).forEach(([k, v]) => url.searchParams.set(k, v));
  const res = await fetch(url.toString(), {
    headers: {
      Authorization: `Zoho-oauthtoken ${token}`,
      orgId: process.env.ZOHO_ORG_ID,
    },
  });
  return res.json();
}

async function deskPost(path, body) {
  const token = await getToken();
  const res = await fetch(`${ZOHO_DESK_BASE}${path}`, {
    method: "POST",
    headers: {
      Authorization: `Zoho-oauthtoken ${token}`,
      orgId: process.env.ZOHO_ORG_ID,
      "Content-Type": "application/json",
    },
    body: JSON.stringify(body),
  });
  return res.json();
}

async function deskPatch(path, body) {
  const token = await getToken();
  const res = await fetch(`${ZOHO_DESK_BASE}${path}`, {
    method: "PATCH",
    headers: {
      Authorization: `Zoho-oauthtoken ${token}`,
      orgId: process.env.ZOHO_ORG_ID,
      "Content-Type": "application/json",
    },
    body: JSON.stringify(body),
  });
  return res.json();
}

const server = new Server(
  { name: "zoho-desk", version: "1.0.0" },
  { capabilities: { tools: {} } }
);

server.setRequestHandler("tools/list", async () => ({
  tools: [
    {
      name: "search_tickets",
      description: "Search Zoho Desk tickets by status, priority, or product",
      inputSchema: {
        type: "object",
        properties: {
          status: { type: "string", description: "Filter by status: Open, On Hold, Escalated, Closed" },
          priority: { type: "string", description: "Filter by priority: Low, Medium, High, Urgent" },
          product: { type: "string", description: "Filter by product name (e.g. PB4000)" },
          limit: { type: "number", default: 50 },
        },
      },
    },
    {
      name: "get_ticket",
      description: "Get a specific Zoho Desk ticket by ID",
      inputSchema: {
        type: "object",
        properties: {
          id: { type: "string", description: "Zoho Desk ticket ID" },
        },
        required: ["id"],
      },
    },
    {
      name: "create_ticket",
      description: "Create a new Zoho Desk ticket. WRITE operation — requires authorization.",
      inputSchema: {
        type: "object",
        properties: {
          subject: { type: "string" },
          description: { type: "string" },
          priority: { type: "string", enum: ["Low", "Medium", "High", "Urgent"] },
          category: { type: "string" },
          product: { type: "string" },
          contactId: { type: "string" },
        },
        required: ["subject", "description"],
      },
    },
    {
      name: "update_ticket",
      description: "Update a Zoho Desk ticket (status, priority, assignee). WRITE operation.",
      inputSchema: {
        type: "object",
        properties: {
          id: { type: "string", description: "Ticket ID" },
          status: { type: "string" },
          priority: { type: "string" },
          assigneeId: { type: "string" },
        },
        required: ["id"],
      },
    },
    {
      name: "add_comment",
      description: "Add a comment to a Zoho Desk ticket. WRITE operation.",
      inputSchema: {
        type: "object",
        properties: {
          ticketId: { type: "string" },
          content: { type: "string" },
          isPublic: { type: "boolean", default: false },
        },
        required: ["ticketId", "content"],
      },
    },
  ],
}));

server.setRequestHandler("tools/call", async (request) => {
  const { name, arguments: args } = request.params;

  switch (name) {
    case "search_tickets": {
      const params = { limit: args.limit || 50, sortBy: "createdTime" };
      if (args.status) params.status = args.status;
      const data = await deskGet("/tickets", params);
      let tickets = data.data || [];
      if (args.priority) tickets = tickets.filter((t) => t.priority === args.priority);
      if (args.product) tickets = tickets.filter((t) => t.product?.name === args.product);
      return { content: [{ type: "text", text: JSON.stringify(tickets, null, 2) }] };
    }
    case "get_ticket": {
      const data = await deskGet(`/tickets/${args.id}`);
      return { content: [{ type: "text", text: JSON.stringify(data, null, 2) }] };
    }
    case "create_ticket": {
      const data = await deskPost("/tickets", args);
      return { content: [{ type: "text", text: JSON.stringify(data, null, 2) }] };
    }
    case "update_ticket": {
      const { id, ...updates } = args;
      const data = await deskPatch(`/tickets/${id}`, updates);
      return { content: [{ type: "text", text: JSON.stringify(data, null, 2) }] };
    }
    case "add_comment": {
      const data = await deskPost(`/tickets/${args.ticketId}/comments`, {
        content: args.content,
        isPublic: args.isPublic || false,
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
