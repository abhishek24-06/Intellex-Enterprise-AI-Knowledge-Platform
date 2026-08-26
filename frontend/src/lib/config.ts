const RAW_BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";

export const API_BASE_URL = RAW_BASE_URL.replace(/\/+$/, "");

export const APP_NAME = "Intellex";
export const APP_TAGLINE = "Enterprise AI knowledge platform";
