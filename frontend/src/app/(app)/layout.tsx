import { Sidebar } from '@/components/layout/sidebar';
import { Topbar } from '@/components/layout/topbar';

export default function AppLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen lg:grid lg:grid-cols-[272px_1fr]">
      {/* На компьютере меню видно всегда, на телефоне открывается кнопкой */}
      <aside className="hidden lg:block lg:h-screen lg:sticky lg:top-0">
        <Sidebar />
      </aside>

      <div className="flex min-h-screen min-w-0 flex-col">
        <Topbar />
        <main className="flex-1 animate-fade-in px-4 py-6 lg:px-8 lg:py-8">
          <div className="mx-auto w-full max-w-6xl">{children}</div>
        </main>
      </div>
    </div>
  );
}
