// nv-client.js
"use strict";
const http = require("http");

const NV_HOST = process.env.NV_HOST || "localhost";
const NV_PORT = parseInt(process.env.NV_PORT || "8900", 10);

function nvGet(path, host = NV_HOST, port = NV_PORT) {
  return new Promise((resolve) => {
    const req = http.request(
      { host, port, path, method: "GET" },
      (res) => {
        let buf = "";
        res.on("data", (c) => (buf += c));
        res.on("end", () => {
          try { resolve(JSON.parse(buf)); } catch { resolve(null); }
        });
      }
    );
    req.on("error", () => resolve(null));
    req.end();
  });
}

function nvPost(path, body, host = NV_HOST, port = NV_PORT) {
  return new Promise((resolve) => {
    const data = JSON.stringify(body);
    const req = http.request(
      {
        host, port, path, method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Content-Length": Buffer.byteLength(data),
        },
      },
      (res) => {
        let buf = "";
        res.on("data", (c) => (buf += c));
        res.on("end", () => {
          try { resolve(JSON.parse(buf)); } catch { resolve({ ok: false }); }
        });
      }
    );
    req.on("error", () => resolve({ ok: false }));
    req.write(data);
    req.end();
  });
}

module.exports = { nvGet, nvPost, NV_HOST, NV_PORT };
