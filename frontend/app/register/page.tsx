import { GalleryVerticalEnd } from "lucide-react"
import { RegisterForm } from "@/components/register-form"

export default function RegisterPage() {
  return (
    <div className="min-h-svh flex flex-col">
      <header className="flex justify-center md:justify-start p-6 md:p-10">
        <a href="#" className="flex items-center gap-2 font-medium">
          <div className="flex h-6 w-6 items-center justify-center rounded-md bg-primary text-primary-foreground">
            <GalleryVerticalEnd className="size-4" />
          </div>
          EveX
        </a>
      </header>

      <main className="flex-1 flex items-center justify-center px-6 py-12">
        <div className="w-full max-w-md bg-white dark:bg-gray-950 p-8 rounded-xl shadow-lg shadow-rose-100 dark:shadow-rose-950/20">
          <RegisterForm />
        </div>
      </main>

      <footer className="py-6 text-center text-sm text-muted-foreground">
        <p>© {new Date().getFullYear()} EveX. All rights reserved.</p>
      </footer>
    </div>
  )
}
