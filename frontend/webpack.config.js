const path = require('path');

module.exports = {
  // ... other webpack configurations
  devServer: {
    setupMiddlewares: (middlewares, devServer) => {
      if (!devServer) {
        throw new Error('webpack-dev-server is not defined');
      }

      // Your middleware setup here
      return middlewares;
    }
  }
}; 