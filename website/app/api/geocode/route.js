import { NextResponse } from "next/server";

// Geocoding runs on the server so the API key isn't exposed to the browser.
// Uses geocode.maps.co if GEOCODE_API_KEY is set, otherwise OpenStreetMap.
const MAPS_CO_URL = "https://geocode.maps.co/search";
const NOMINATIM_URL = "https://nominatim.openstreetmap.org/search";
const TIMEOUT_MS = 10_000;

// Nominatim requires a User-Agent
const USER_AGENT = "Annapoorna/1.0 (crop health assistant)";

const ALLOW_FALLBACKS = process.env.ALLOW_KEYLESS_FALLBACKS !== "false";

function toBoundingBox(result) {
  // [south, north, west, east] as strings
  const raw = result?.boundingbox;
  if (!Array.isArray(raw) || raw.length !== 4) return null;

  const numbers = raw.map(Number);
  return numbers.every(Number.isFinite) ? numbers : null;
}

async function geocodeViaMapsCo(address) {
  const apiKey = process.env.GEOCODE_API_KEY;
  if (!apiKey) return { error: "GEOCODE_API_KEY is not configured." };

  const url = `${MAPS_CO_URL}?q=${encodeURIComponent(address)}&api_key=${apiKey}`;
  try {
    const response = await fetch(url, { signal: AbortSignal.timeout(TIMEOUT_MS) });
    if (!response.ok) {
      return { error: `geocode.maps.co returned ${response.status}.` };
    }
    const results = await response.json();
    const boundingBox = toBoundingBox(results?.[0]);
    if (!boundingBox) return { error: "No match from geocode.maps.co." };

    return {
      boundingBox,
      displayName: results[0].display_name ?? address,
      source: "geocode.maps.co",
    };
  } catch {
    // don't return the error, it can contain the key
    return { error: "geocode.maps.co is unreachable." };
  }
}

async function geocodeViaNominatim(address) {
  const url =
    `${NOMINATIM_URL}?q=${encodeURIComponent(address)}` +
    `&format=json&limit=1&addressdetails=0`;
  try {
    const response = await fetch(url, {
      headers: { "User-Agent": USER_AGENT, Accept: "application/json" },
      signal: AbortSignal.timeout(TIMEOUT_MS),
    });
    if (!response.ok) {
      return { error: `Nominatim returned ${response.status}.` };
    }
    const results = await response.json();
    const boundingBox = toBoundingBox(results?.[0]);
    if (!boundingBox) return { error: "No match from OpenStreetMap." };

    return {
      boundingBox,
      displayName: results[0].display_name ?? address,
      source: "OpenStreetMap (Nominatim)",
    };
  } catch {
    return { error: "OpenStreetMap is unreachable." };
  }
}

export async function GET(request) {
  const address = request.nextUrl.searchParams.get("address");

  if (!address || !address.trim()) {
    return NextResponse.json({ error: "An address is required." }, { status: 400 });
  }

  const primary = await geocodeViaMapsCo(address);
  if (!primary.error) return NextResponse.json(primary);

  if (!ALLOW_FALLBACKS) {
    return NextResponse.json(
      { error: "Geocoding is not configured. Set GEOCODE_API_KEY." },
      { status: 503 }
    );
  }

  const fallback = await geocodeViaNominatim(address);
  if (!fallback.error) {
    return NextResponse.json({ ...fallback, fallbackReason: primary.error });
  }

  return NextResponse.json(
    {
      error:
        "Could not locate that address. Try a more specific one, " +
        "or use the demo farmer to skip registration.",
      details: [primary.error, fallback.error],
    },
    { status: 404 }
  );
}
