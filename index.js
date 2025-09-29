// index.js
import { SquareClient, SquareEnvironment, SquareError } from "square";
import dotenv from "dotenv";
dotenv.config();
const ENV =SquareEnvironment.Production

async function main() {
  // IMPORTANT: use `token`, not `accessToken`
  const client = new SquareClient({
    token: process.env.SQUARE_ACCESS_TOKEN,
    environment: ENV,
  });

  try {
    // quick smoke test: list locations to verify auth + environment
    const locRes = await client.locations.list();
    console.log(
      "Locations:",
      locRes.locations?.map(l => `${l.id} • ${l.name}`)
    );

    // now list invoices
    const invRes = await client.invoices.list({
      locationId: process.env.SQUARE_LOCATION_ID,
      limit: 3,
    });

    console.log("Invoices list:", JSON.stringify(invRes, null, 2));
  } catch (error) {
    if (error instanceof SquareError) {
      console.error("SquareError:", error.statusCode, JSON.stringify(error.errors, null, 2));
    } else {
      console.error("Unexpected error:", error);
    }
  }
}

main();
