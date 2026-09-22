import { ImageResponse } from "next/og";

export const alt = "BULLCULTURE · Suplementación para fuerza real";
export const size = { width: 1200, height: 630 };
export const contentType = "image/png";

export default function OpengraphImage() {
  return new ImageResponse(
    (
      <div
        style={{
          width: "100%",
          height: "100%",
          display: "flex",
          flexDirection: "column",
          justifyContent: "center",
          padding: "80px",
          background: "radial-gradient(120% 120% at 100% 0%, #131E28 0%, #0A0E14 55%)",
          color: "#F8FAFB",
          fontFamily: "sans-serif",
        }}
      >
        <div
          style={{
            display: "flex",
            fontSize: 26,
            letterSpacing: 8,
            color: "#6C93B6",
            fontWeight: 700,
          }}
        >
          PROTEÍNA · CREATINA · VITAMINAS · OMEGA 3
        </div>
        <div
          style={{
            display: "flex",
            flexDirection: "column",
            marginTop: 24,
            fontSize: 92,
            fontWeight: 800,
            lineHeight: 1,
          }}
        >
          <span>FUERZA REAL.</span>
          <span>RENDIMIENTO CONSTANTE.</span>
        </div>
        <div style={{ display: "flex", marginTop: 40, alignItems: "center" }}>
          <div
            style={{
              display: "flex",
              width: 60,
              height: 8,
              background: "#88BEDF",
              borderRadius: 4,
              marginRight: 20,
            }}
          />
          <span style={{ fontSize: 34, fontWeight: 700, letterSpacing: 2 }}>
            BULLCULTURE
          </span>
          <span style={{ fontSize: 20, color: "#A0A8B3", marginLeft: 16 }}>
            Bogotá · Colombia
          </span>
        </div>
      </div>
    ),
    size
  );
}
