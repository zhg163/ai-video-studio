import axios from 'axios'

const apiClient = axios.create({
  baseURL: '/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
})

// Response interceptor: unwrap ApiResponse envelope { code, message, data }
apiClient.interceptors.response.use(
  (response) => {
    // Backend returns { code: 0, message: "ok", data: ... }
    if (response.data && typeof response.data === 'object' && 'code' in response.data) {
      if (response.data.code !== 0) {
        return Promise.reject(new Error(response.data.message || 'API error'))
      }
      // Return a synthetic response with data unwrapped
      return { ...response, data: response.data.data }
    }
    return response
  },
  (error) => {
    const message =
      error.response?.data?.message ||
      error.response?.data?.detail ||
      error.message ||
      'Unknown error'
    return Promise.reject(new Error(message))
  }
)

export default apiClient
