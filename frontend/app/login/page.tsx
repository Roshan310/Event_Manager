import { GalleryVerticalEnd } from "lucide-react"

import { LoginForm } from "@/components/login-form"
import { AnimatedBackground } from "@/components/animated-background"

interface WelcomeContentProps {
  title?: string
  description?: string
}

function WelcomeContent({
  title = "Welcome back",
  description = "Sign in to access your dashboard and manage your projects with ease.",
}: WelcomeContentProps) {
  return (
    <div className="max-w-md">
      <h2 className="text-3xl font-bold text-gray-800 dark:text-gray-200 mb-4">{title}</h2>
      <p className="text-lg text-gray-600 dark:text-gray-400 leading-relaxed">{description}</p>
    </div>
  )
}

export default function LoginPage() {
  // 🎯 Easily customize these values:
  const welcomeTitle = "Not Logged in yet?"
  const welcomeDescription = "Log in to access all your personal events."

  // 💡 Or try these alternatives:
  // const welcomeTitle = "Hello Again!"
  // const welcomeDescription = "We're excited to see you return. Please sign in to continue your journey."

  // const welcomeTitle = "Ready to Continue?"
  // const welcomeDescription = "Access your personalized workspace and pick up right where you left off."

  return (
    <div className="grid min-h-svh lg:grid-cols-[1fr_1fr]">
      <div className="flex flex-col gap-4 p-6 md:p-10">
        <div className="flex justify-center gap-2 md:justify-start">
          <a href="#" className="flex items-center gap-2 font-medium">
            <div className="flex h-6 w-6 items-center justify-center rounded-md bg-primary text-primary-foreground">
              <GalleryVerticalEnd className="size-4" />
            </div>
            EveX
          </a>
        </div>
        <div className="flex flex-1 items-center justify-center">
          <div className="w-full max-w-xs">
            <LoginForm />
          </div>
        </div>
      </div>
      <div className="relative hidden lg:block">
        <AnimatedBackground />

        {/* Gradient transition overlay */}
        <div className="absolute inset-y-0 left-0 w-20 bg-gradient-to-r from-background via-background/80 to-transparent z-20" />

        {/* Content overlay */}
        <div className="relative z-10 flex h-full flex-col justify-center p-12 pl-32">
          <WelcomeContent title={welcomeTitle} description={welcomeDescription} />
        </div>
      </div>
    </div>
  )
}
