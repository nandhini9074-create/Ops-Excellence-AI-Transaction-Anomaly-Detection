export interface Env {
  DB: D1Database;
  API_KEY: string;
}

export default {
  async fetch(request: Request, env: Env, ctx: ExecutionContext): Promise<Response> {
    const url = new URL(request.url);
    const method = request.method;

    // Validate API Key
    const authHeader = request.headers.get("X-API-Key");
    // For local dev without secrets configured, allow if API_KEY is not set.
    if (env.API_KEY && authHeader !== env.API_KEY) {
      return new Response("Unauthorized", { status: 401 });
    }

    try {
      if (url.pathname === "/historical/transactions" && method === "POST") {
        return await handleBatchInsert(request, env);
      } else if (url.pathname === "/historical/transactions" && method === "GET") {
        return await handleQuery(url, env);
      } else if (url.pathname === "/historical/window" && method === "GET") {
        return await handleWindowQuery(url, env);
      }

      return new Response("Not Found", { status: 404 });
    } catch (e: any) {
      return new Response(JSON.stringify({ error: e.message }), {
        status: 500,
        headers: { "Content-Type": "application/json" }
      });
    }
  },
};

async function handleBatchInsert(request: Request, env: Env): Promise<Response> {
  const data: any = await request.json();
  if (!data.transactions || !Array.isArray(data.transactions)) {
    return new Response("Invalid payload", { status: 400 });
  }

  const stmts = data.transactions.map((tx: any) => {
    return env.DB.prepare(`
      INSERT INTO historical_transactions (
        id, transaction_id, transaction_no, group_id, group_transaction_id, payout_transaction_id,
        outlet_id, merchant_id, profile_id, transaction_timestamp, posting_timestamp,
        txn_date, txn_hour, created_on, last_updated_on, silver_updated_at,
        transaction_amount, card_scheme, merchant_name, outlet_name, outlet_status, archived_at
      ) VALUES (
        ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now')
      )
      ON CONFLICT (id) DO NOTHING;
    `).bind(
      tx.id || crypto.randomUUID(),
      tx.transaction_id || null,
      tx.transaction_no || null,
      tx.group_id || null,
      tx.group_transaction_id || null,
      tx.payout_transaction_id || null,
      tx.outlet_id,
      tx.merchant_id,
      tx.profile_id,
      tx.transaction_timestamp,
      tx.posting_timestamp || null,
      tx.txn_date,
      tx.txn_hour,
      tx.created_on || null,
      tx.last_updated_on || null,
      tx.silver_updated_at || null,
      tx.transaction_amount,
      tx.card_scheme || null,
      tx.merchant_name || null,
      tx.outlet_name || null,
      tx.outlet_status || null
    );
  });

  const results = await env.DB.batch(stmts);
  return new Response(JSON.stringify({ success: true, processed: results.length }), {
    status: 201,
    headers: { "Content-Type": "application/json" }
  });
}

async function handleQuery(url: URL, env: Env): Promise<Response> {
  const outletId = url.searchParams.get("outlet_id");
  const limit = parseInt(url.searchParams.get("limit") || "100", 10);
  
  let query = `SELECT * FROM historical_transactions`;
  let params: any[] = [];
  
  if (outletId) {
    query += ` WHERE outlet_id = ?`;
    params.push(outletId);
  }
  
  query += ` ORDER BY transaction_timestamp DESC LIMIT ?`;
  params.push(limit);
  
  const { results } = await env.DB.prepare(query).bind(...params).all();
  return new Response(JSON.stringify({ results }), {
    status: 200,
    headers: { "Content-Type": "application/json" }
  });
}

async function handleWindowQuery(url: URL, env: Env): Promise<Response> {
  const outletId = url.searchParams.get("outlet_id");
  const days = parseInt(url.searchParams.get("days") || "90", 10);
  
  if (!outletId) {
    return new Response("Missing outlet_id", { status: 400 });
  }
  
  const query = `
    SELECT 
      transaction_amount, 
      transaction_timestamp, 
      txn_date, 
      txn_hour,
      card_scheme
    FROM historical_transactions
    WHERE outlet_id = ? 
    AND transaction_timestamp >= datetime('now', '-' || ? || ' days')
    ORDER BY transaction_timestamp ASC
  `;
  
  const { results } = await env.DB.prepare(query).bind(outletId, days).all();
  return new Response(JSON.stringify({ results }), {
    status: 200,
    headers: { "Content-Type": "application/json" }
  });
}
