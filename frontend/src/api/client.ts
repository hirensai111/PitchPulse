import axios from "axios";

const baseURL = import.meta.env.DEV ? "http://localhost:8000" : "";

export const apiClient = axios.create({
  baseURL,
  headers: {
    "Content-Type": "application/json",
  },
});
