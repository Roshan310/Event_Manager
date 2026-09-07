"use client";
import Link from "next/link";
import Image from "next/image";
import { useState } from "react";
import { useHydrated } from "@/lib/hydration";
import { useRouter, useSearchParams } from "next/navigation";
import { useQueryClient } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { ArrowRight, Eye, EyeOff, ArrowLeft } from "lucide-react";
import { authenticate } from "@/lib/api";
import type { Session } from "@/lib/types";
import { Logo } from "./shell";
import { Button } from "./ui/button";
const schema = z.object({
  name: z.string().optional(),
  email: z.email("Enter a valid email address."),
  password: z.string().min(1, "Enter your password.").max(128),
});
type Values = z.infer<typeof schema>;
export function AuthForm({ registerMode = false }: { registerMode?: boolean }) {
  const hydrated = useHydrated();
  const [visible, setVisible] = useState(false);
  const [error, setError] = useState("");
  const router = useRouter();
  const params = useSearchParams();
  const client = useQueryClient();
  const {
    register,
    handleSubmit,
    setError: fieldError,
    formState: { errors, isSubmitting },
  } = useForm<Values>({ resolver: zodResolver(schema) });
  const requested = params.get("next") ?? "/";
  const next =
    requested.startsWith("/") &&
    !requested.startsWith("//") &&
    !requested.includes("\\")
      ? requested
      : "/";
  async function submit(values: Values) {
    setError("");
    if (registerMode) {
      if (
        !values.name ||
        values.name.trim().length < 2 ||
        values.name.length > 120
      ) {
        fieldError("name", { message: "Use 2–120 characters for your name." });
        return;
      }
      if (values.password.length < 10) {
        fieldError("password", { message: "Use at least 10 characters." });
        return;
      }
    }
    try {
      let session: Session;
      if (registerMode) {
        await authenticate("register", values);
        try {
          session = await authenticate("login", {
            email: values.email,
            password: values.password,
          });
        } catch {
          router.push("/login?registered=1&next=" + encodeURIComponent(next));
          return;
        }
      } else
        session = await authenticate("login", {
          email: values.email,
          password: values.password,
        });
      await client.cancelQueries();
      client.removeQueries({ predicate: (q) => q.queryKey[0] !== "session" });
      client.setQueryData(["session"], session);
      router.replace(next);
      router.refresh();
    } catch (e) {
      setError((e as Error).message);
    }
  }
  return (
    <div className="auth-layout">
      <section className="auth-main">
        <Logo />
        <div className="auth-form-wrap">
          <Link href="/" className="back-link">
            <ArrowLeft size={16} />
            Back to exploring
          </Link>
          <span className="eyebrow">YOUR PEOPLE ARE OUT THERE</span>
          <h1>{registerMode ? "Good things start here." : "Welcome back."}</h1>
          <p className="auth-intro">
            {registerMode
              ? "A new experience. A new connection. All it takes is you."
              : "Your next great experience is just around the corner."}
          </p>
          <form
            onSubmit={handleSubmit(submit)}
            className="form-stack"
            noValidate
          >
            {registerMode && (
              <label>
                Full name
                <input
                  disabled={!hydrated || isSubmitting}
                  autoComplete="name"
                  placeholder="Alex Chen"
                  {...register("name")}
                  aria-invalid={!!errors.name}
                />
                {errors.name && (
                  <span className="field-error">{errors.name.message}</span>
                )}
              </label>
            )}
            <label>
              Email address
              <input
                disabled={!hydrated || isSubmitting}
                type="email"
                autoComplete="email"
                placeholder="you@example.com"
                {...register("email")}
                aria-invalid={!!errors.email}
              />
              {errors.email && (
                <span className="field-error">{errors.email.message}</span>
              )}
            </label>
            <label>
              <span id="password-label">Password</span>
              <span className="password-input">
                <input
                  disabled={!hydrated || isSubmitting}
                  aria-labelledby="password-label"
                  type={visible ? "text" : "password"}
                  autoComplete={
                    registerMode ? "new-password" : "current-password"
                  }
                  placeholder={
                    registerMode
                      ? "At least 10 characters"
                      : "Enter your password"
                  }
                  {...register("password")}
                  aria-invalid={!!errors.password}
                />
                <button
                  type="button"
                  aria-label={visible ? "Hide password" : "Show password"}
                  onClick={() => setVisible(!visible)}
                >
                  {visible ? <EyeOff size={18} /> : <Eye size={18} />}
                </button>
              </span>
              {errors.password && (
                <span className="field-error">{errors.password.message}</span>
              )}
            </label>
            {error && (
              <div role="alert" className="form-error">
                {error}
              </div>
            )}
            {params.has("registered") && (
              <p className="success-message">
                Your account is ready. Sign in to continue.
              </p>
            )}
            <Button
              className="auth-submit"
              type="submit"
              disabled={!hydrated || isSubmitting}
            >
              {isSubmitting
                ? "One moment…"
                : registerMode
                  ? "Create your account"
                  : "Sign in"}
              <ArrowRight size={17} />
            </Button>
          </form>
          <p className="auth-switch">
            {registerMode
              ? "Already part of the community?"
              : "New to Evently?"}{" "}
            <Link
              href={
                (registerMode ? "/login" : "/register") +
                "?next=" +
                encodeURIComponent(next)
              }
            >
              {registerMode ? "Sign in" : "Create an account"}
            </Link>
          </p>
          <p className="auth-note">
            {registerMode
              ? "Your account starts with attendee access."
              : "Need help accessing your account? Contact your administrator."}
          </p>
        </div>
        <small className="auth-footer">
          A little more connection. A lot more possibility.
        </small>
      </section>
      <aside className="auth-visual">
        <Image
          src="/images/hero.jpg"
          alt="People enjoying a live event together"
          fill
          priority
          sizes="50vw"
        />
        <div className="auth-visual-shade" />
        <div className="auth-visual-copy">
          <span className="auth-photo-label">
            GET OUT THERE. FEEL SOMETHING.
          </span>
          <h2>
            Life happens
            <br />
            when we
            <br />
            <em>come together.</em>
          </h2>
          <p>Find the moments that become your favorite stories.</p>
          <span className="auth-decoration">✳</span>
        </div>
      </aside>
    </div>
  );
}
