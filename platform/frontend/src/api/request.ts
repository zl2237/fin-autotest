import axios from 'axios'

const request = axios.create({
  baseURL: '/api',
})

request.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('platform_token')
    if (token) {
      config.headers.Authorization = token
    }
    return config
  },
  (error) => Promise.reject(error)
)

request.interceptors.response.use(
  (res) => res,
  (err) => {
    const isLoginPage = window.location.pathname.startsWith('/login')
    if (err.response?.status === 401 && !isLoginPage) {
      localStorage.removeItem('platform_token')
      localStorage.removeItem('platform_username')
      window.location.href = '/login'
    }
    return Promise.reject(err)
  }
)

export default request
