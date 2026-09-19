import type { Metadata } from "next";
import "../styles/globals.css";

export const metadata: Metadata = {
  title: "SRMAP SAGE — Student Assistance & Guidance Engine",
  description: "Official, verified AI information and guidance platform for SRM University-AP students.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>
        <div style={{ display: "flex", flexDirection: "column", minHeight: "100vh" }}>
          {children}
        </div>
      </body>
    </html>
  );
}
