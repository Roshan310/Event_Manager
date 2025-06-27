export async function getCurrentUser() {
  const token = localStorage.getItem("token")
  if (!token) return null

  const res = await fetch("http://localhost:8000/users/me", {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  })

  if (!res.ok) return null
  console.log("Current user fetched successfully")
  return await res.json()
}

export function logout() {
  localStorage.removeItem("token")
  console.log("User logged out successfully")
  window.location.href = "/login" // Redirect to login page
}