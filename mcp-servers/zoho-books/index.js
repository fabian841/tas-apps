const { Server } = require("@modelcontextprotocol/sdk/server/index.js");
const { StdioServerTransport } = require("@modelcontextprotocol/sdk/server/stdio.js");

// Zoho Books MCP Server for LIFE OS Company Layer
// Exposes Zoho Books invoice operations as MCP tools.

const ZOHO_BOOKS_BASE = "https://books.zoho.com.au/api/v3";

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

async function booksGet(path, params = {}) {
  const token = await getToken();
  const url = new URL(`${ZOHO_BOOKS_BASE}${path}`);
  url.searchParams.set("organization_id", process.env.ZOHO_ORG_ID);
  Object.entries(params).forEach(([k, v]) => url.searchParams.set(k, v));
  const res = await fetch(url.toString(), {
    headers: { Authorization: `Zoho-oauthtoken ${token}` },
  });
  return res.json();
}

const server = new Server(
  { name: "zoho-books", version: "1.0.0" },
  { capabilities: { tools: {} } }
);

server.setRequestHandler("tools/list", async () => ({
  tools: [
    {
      name: "list_invoices",
      description: "List Zoho Books invoices with optional filters",
      inputSchema: {
        type: "object",
        properties: {
          status: { type: "string", description: "Filter: draft, sent, overdue, paid, void" },
          customer_name: { type: "string", description: "Filter by customer name" },
          date_start: { type: "string", description: "Invoice date from (YYYY-MM-DD)" },
          date_end: { type: "string", description: "Invoice date to (YYYY-MM-DD)" },
          per_page: { type: "number", default: 50 },
        },
      },
    },
    {
      name: "get_invoice",
      description: "Get a specific Zoho Books invoice by ID",
      inputSchema: {
        type: "object",
        properties: {
          id: { type: "string", description: "Zoho Books invoice ID" },
        },
        required: ["id"],
      },
    },
    {
      name: "list_overdue",
      description: "List all overdue invoices, sorted by amount descending",
      inputSchema: {
        type: "object",
        properties: {
          limit: { type: "number", default: 50 },
        },
      },
    },
    {
      name: "search_invoices",
      description: "Search invoices by invoice number or reference",
      inputSchema: {
        type: "object",
        properties: {
          search_text: { type: "string", description: "Invoice number or reference to search" },
        },
        required: ["search_text"],
      },
    },
  ],
}));

server.setRequestHandler("tools/call", async (request) => {
  const { name, arguments: args } = request.params;

  switch (name) {
    case "list_invoices": {
      const params = { per_page: args.per_page || 50 };
      if (args.status) params.status = args.status;
      if (args.customer_name) params.customer_name = args.customer_name;
      if (args.date_start) params.date_start = args.date_start;
      if (args.date_end) params.date_end = args.date_end;
      const data = await booksGet("/invoices", params);
      return { content: [{ type: "text", text: JSON.stringify(data.invoices || [], null, 2) }] };
    }
    case "get_invoice": {
      const data = await booksGet(`/invoices/${args.id}`);
      return { content: [{ type: "text", text: JSON.stringify(data.invoice || {}, null, 2) }] };
    }
    case "list_overdue": {
      const data = await booksGet("/invoices", { status: "overdue", per_page: args.limit || 50, sort_column: "total", sort_order: "D" });
      return { content: [{ type: "text", text: JSON.stringify(data.invoices || [], null, 2) }] };
    }
    case "search_invoices": {
      const data = await booksGet("/invoices", { search_text: args.search_text });
      return { content: [{ type: "text", text: JSON.stringify(data.invoices || [], null, 2) }] };
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
