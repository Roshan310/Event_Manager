export function AnimatedBackground() {
  return (
    <div className="absolute inset-0 overflow-hidden">
      {/* Animated gradient background */}
      <div className="absolute inset-0 bg-gradient-to-br from-rose-50 via-pink-50 to-red-50 dark:from-rose-950 dark:via-pink-950 dark:to-red-950" />

      {/* Floating geometric shapes */}
      <div className="absolute inset-0">
        {/* Large circle */}
        <div
          className="absolute -top-40 -right-40 h-80 w-80 rounded-full bg-gradient-to-br from-rose-200/30 to-pink-200/30 dark:from-rose-800/20 dark:to-pink-800/20 animate-pulse"
          style={{ animationDuration: "4s" }}
        />

        {/* Medium circle */}
        <div
          className="absolute top-1/3 -left-20 h-60 w-60 rounded-full bg-gradient-to-br from-pink-200/20 to-red-200/20 dark:from-pink-800/15 dark:to-red-800/15 animate-bounce"
          style={{ animationDuration: "6s" }}
        />

        {/* Small floating elements */}
        <div
          className="absolute top-1/4 right-1/4 h-4 w-4 rounded-full bg-rose-300/40 dark:bg-rose-600/30 animate-ping"
          style={{ animationDuration: "3s" }}
        />
        <div
          className="absolute bottom-1/3 left-1/3 h-6 w-6 rounded-full bg-pink-300/40 dark:bg-pink-600/30 animate-ping"
          style={{ animationDuration: "4s", animationDelay: "1s" }}
        />
        <div
          className="absolute top-2/3 right-1/3 h-3 w-3 rounded-full bg-red-300/40 dark:bg-red-600/30 animate-ping"
          style={{ animationDuration: "5s", animationDelay: "2s" }}
        />
      </div>

      {/* Animated mesh overlay */}
      <div className="absolute inset-0 opacity-30">
        <svg className="h-full w-full" viewBox="0 0 400 400" xmlns="http://www.w3.org/2000/svg">
          <defs>
            <linearGradient id="grad1" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" style={{ stopColor: "#F43F5E", stopOpacity: 0.1 }}>
                <animate
                  attributeName="stop-color"
                  values="#F43F5E;#EC4899;#EF4444;#F43F5E"
                  dur="8s"
                  repeatCount="indefinite"
                />
              </stop>
              <stop offset="100%" style={{ stopColor: "#EC4899", stopOpacity: 0.1 }}>
                <animate
                  attributeName="stop-color"
                  values="#EC4899;#EF4444;#F43F5E;#EC4899"
                  dur="8s"
                  repeatCount="indefinite"
                />
              </stop>
            </linearGradient>
          </defs>
          <path d="M0,100 Q100,50 200,100 T400,100 L400,300 Q300,350 200,300 T0,300 Z" fill="url(#grad1)">
            <animateTransform
              attributeName="transform"
              type="translate"
              values="0,0;10,-5;0,0"
              dur="6s"
              repeatCount="indefinite"
            />
          </path>
        </svg>
      </div>
    </div>
  )
}
