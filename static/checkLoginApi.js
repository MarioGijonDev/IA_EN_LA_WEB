


const checkLoginApi = async () => {
  try {

      const resToken = await fetch('http://localhost:3000/api/v1/auth/refresh', {
          method: 'GET',
          credentials: 'include'
      })

      const { token } = await resToken.json()

      const res = await fetch('http://localhost:3000/api/v1/auth/protected', {
          method: 'GET',
          headers: {
              'Content-Type': 'application/json',
              Authorization: `Bearer ${token}`
          }
      })

      const response = await res.json()

      if(response.status === 'bad')
        return false

      return true

  } catch (e) {

      console.log(e)

  }
}

checkLoginApi().then(response => {
  if (response.status === 'bad')
      document.getElementById('body').innerHTML =
      `
        <h1>You are not loggin in</h1>
        <section class="portfolio-experiment">
        <a href="http://localhost:5173/">
          <span class="text">Get log in for free</span>
          <span class="line -right"></span>
          <span class="line -top"></span>
          <span class="line -left"></span>
          <span class="line -bottom"></span>
        </a>
        </section>
      `
});