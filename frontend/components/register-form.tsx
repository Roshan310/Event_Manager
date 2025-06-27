'use client'
import type React from "react"
import { useState } from "react"
import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"

export function RegisterForm({ className, ...props }: React.ComponentPropsWithoutRef<"form">) {

  const [formData, setFormData] = useState({ name: "", email: "", password: "" })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError(null)

    try {
      const res = await fetch("http://localhost:8000/users", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(formData),
      })
      const data = await res.json()
      console.log("Response data:", data)
      if (!res.ok) {
        setError(data.detail || "Registration failed")
        return
      }
      console.log("Registration successful", data)
      localStorage.setItem("token", data.access_token)
      window.location.href = "/dashboard" // redirect to protected page
    } catch (err) {
      console.error("Registration error:", err)
      setError("An unexpected error occurred. Please try again.")
    } finally {
      setLoading(false) 
    }
  }
  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {  
    const { name, value } = e.target
    setFormData((prev) => ({ ...prev, [name]: value }))
  }

  return (
    <form onSubmit={handleSubmit} className={cn("flex flex-col gap-6", className)} {...props}>
      <div className="flex flex-col items-center gap-2 text-center">
        <h1 className="text-2xl font-bold">Create your account</h1>
        <p className="text-balance text-sm text-muted-foreground">Enter your details below to create your account</p>
      </div>
      <div className="grid gap-6">
        <div className="grid gap-2">
          <Label htmlFor="name">Full Name</Label>
          <Input
            id="name"
            name="name"
            type="text"
            placeholder="Your full name"
            value={formData.name}
            onChange={handleChange}
            required
            className="transition-all duration-300 hover:scale-[1.02] hover:shadow-md hover:border-rose-300 focus:scale-[1.02] focus:shadow-lg focus:border-rose-400 dark:hover:border-rose-600 dark:focus:border-rose-500"
          />
        </div>
        <div className="grid gap-2">
          <Label htmlFor="email">Email</Label>
          <Input
            id="email"
            name="email"
            type="email"
            placeholder="email"
            value={formData.email}
            onChange={handleChange}
            required
            className="transition-all duration-300 hover:scale-[1.02] hover:shadow-md hover:border-rose-300 focus:scale-[1.02] focus:shadow-lg focus:border-rose-400 dark:hover:border-rose-600 dark:focus:border-rose-500"
          />
        </div>
        <div className="grid gap-2">
          <Label htmlFor="password">Password</Label>
          <Input
            id="password"
            type="password"
            name="password"
            placeholder="Create a strong password"
            value={formData.password}
            onChange={handleChange}
            required
            className="transition-all duration-300 hover:scale-[1.02] hover:shadow-md hover:border-rose-300 focus:scale-[1.02] focus:shadow-lg focus:border-rose-400 dark:hover:border-rose-600 dark:focus:border-rose-500"
          />
        </div>
        <Button
          type="submit"
          className="w-full transition-all duration-300 hover:scale-[1.02] hover:shadow-lg hover:shadow-rose-500/25 active:scale-[0.98] transform-gpu"
        >
          Create Account
        </Button>
        {error && (
          <p className="text-sm text-red-500 text-center">{error}</p>
        )}
      </div>
      <div className="text-center text-sm">
        Already have an account?{" "}
        <a
          href="/login"
          className="underline underline-offset-4 transition-colors duration-200 hover:text-rose-600 dark:hover:text-rose-400"
        >
          Sign in
        </a>
      </div>
    </form>
  )
}
