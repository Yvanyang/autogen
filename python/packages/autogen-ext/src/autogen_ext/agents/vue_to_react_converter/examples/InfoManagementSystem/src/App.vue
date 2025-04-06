<template>
  <div id="app">
    <header>
      <h1>Information Management System</h1>
    </header>
    <main>
      <div class="container">
        <PageManager />
      </div>
    </main>
  </div>
</template>

<script>
import PageManager from './components/PageManager.vue';

export default {
  name: 'App',
  components: {
    PageManager
  }
}
</script>

<style>
#app {
  font-family: 'Avenir', Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  color: #2c3e50;
  margin: 0;
  padding: 0;
}

header {
  background-color: #42b983;
  color: white;
  padding: 1rem;
  text-align: center;
}

.container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 2rem;
}
</style>
