import "./globals.css";

export const metadata = {
  title: "MyNotes RAG - Chat with your handwritten knowledge",
  description: "Ask questions from your handwritten AI, Python & SQL notes.",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en" className="dark">
      <body className="bg-[#080c14] text-slate-100 antialiased selection:bg-indigo-500 selection:text-white min-h-screen">
        {children}
      </body>
    </html>
  );
}
