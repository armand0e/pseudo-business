class LoadBalancer {
  constructor() {
    this.servers = [];
    this.currentIndex = 0;
  }

  /**
   * Add a server to the load balancer pool
   * @param {string} url - The URL of the backend service
   */
  addServer(url) {
    this.servers.push(url);
  }

  /**
   * Get the next server in round-robin fashion
   * @returns {string} - The selected server URL
   */
  getNextServer() {
    if (this.servers.length === 0) {
      throw new Error('No servers available');
    }

    const server = this.servers[this.currentIndex];
    this.currentIndex = (this.currentIndex + 1) % this.servers.length;
    return server;
  }
}

module.exports = LoadBalancer;