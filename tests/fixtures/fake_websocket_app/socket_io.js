const { Server } = require('socket.io');
const io = new Server(3000);

io.on('connection', (socket) => {
  console.log('user connected');

  socket.on('chat message', (msg) => {
    io.emit('chat message', msg);
  });

  socket.on('join room', (room) => {
    socket.join(room);
  });

  socket.on('typing', (data) => {
    socket.broadcast.emit('typing', data);
  });

  socket.on('disconnect', () => {
    console.log('user disconnected');
  });
});
