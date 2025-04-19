import React, { useState, useRef, useEffect } from 'react';
import { 
  Container, 
  Box, 
  TextField, 
  Button, 
  Typography, 
  Paper,
  CircularProgress,
  Grid,
  ThemeProvider,
  createTheme,
  CssBaseline,
  useMediaQuery
} from '@mui/material';
import { useDropzone } from 'react-dropzone';
import axios from 'axios';
import { Send as SendIcon, CloudUpload as CloudUploadIcon, AllInclusive as InfinityIcon } from '@mui/icons-material';

// API Configuration
const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

// Custom theme
const theme = createTheme({
  palette: {
    primary: {
      main: '#1E4D8C',
      light: '#2E6BC4',
      dark: '#153761',
    },
    secondary: {
      main: '#FF6B6B',
      light: '#FF8E8E',
      dark: '#FF4848',
    },
    background: {
      default: '#F0F4F8',
      paper: '#FFFFFF',
    },
  },
  typography: {
    fontFamily: '"Poppins", "Roboto", "Helvetica", "Arial", sans-serif',
    h4: {
      fontWeight: 700,
      background: 'linear-gradient(45deg, #1E4D8C 30%, #2E6BC4 90%)',
      WebkitBackgroundClip: 'text',
      WebkitTextFillColor: 'transparent',
      letterSpacing: '0.5px',
    },
  },
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: 12,
          textTransform: 'none',
          fontWeight: 600,
          boxShadow: 'none',
          '&:hover': {
            boxShadow: '0 4px 12px rgba(30, 77, 140, 0.2)',
          },
        },
      },
    },
    MuiPaper: {
      styleOverrides: {
        root: {
          borderRadius: 16,
          boxShadow: '0 4px 20px rgba(0, 0, 0, 0.05)',
        },
      },
    },
    MuiTextField: {
      styleOverrides: {
        root: {
          '& .MuiOutlinedInput-root': {
            borderRadius: 12,
            backgroundColor: '#FFFFFF',
            '&:hover': {
              boxShadow: '0 2px 8px rgba(30, 77, 140, 0.1)',
            },
            '&.Mui-focused': {
              boxShadow: '0 4px 12px rgba(30, 77, 140, 0.15)',
            },
          },
        },
      },
    },
  },
});

interface Message {
  type: 'user' | 'bot';
  content: string;
  imageUrl?: string;
}

const App: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [location, setLocation] = useState('');
  const [loading, setLoading] = useState(false);
  const [lastAnalysis, setLastAnalysis] = useState<any>(null);
  const messagesEndRef = useRef<null | HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const onDrop = async (acceptedFiles: File[]) => {
    if (acceptedFiles.length === 0) return;

    setLoading(true);
    const file = acceptedFiles[0];
    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await axios.post(`${API_URL}/upload-image`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      if (response.data.last_analysis) {
        setLastAnalysis(response.data.last_analysis);
      }

      setMessages(prev => [...prev, 
        { type: 'user', content: 'Uploaded image for analysis', imageUrl: response.data.image_url },
        { type: 'bot', content: response.data.response }
      ]);
    } catch (error) {
      console.error('Error uploading image:', error);
      setMessages(prev => [...prev, 
        { type: 'bot', content: 'Sorry, there was an error processing your image. Please try again.' }
      ]);
    } finally {
      setLoading(false);
    }
  };

  const { getRootProps, getInputProps, isDragActive } = useDropzone({ 
    onDrop,
    accept: {
      'image/*': ['.jpeg', '.jpg', '.png', '.gif']
    },
    maxFiles: 1
  });

  const handleSendMessage = async () => {
    if (!input.trim()) return;

    const userMessage = input.trim();
    setInput('');
    setMessages(prev => [...prev, { type: 'user', content: userMessage }]);
    setLoading(true);

    try {
      const response = await axios.post(`${API_URL}/chat`, {
        message: userMessage,
        location: location || undefined,
        last_analysis: lastAnalysis
      });

      setMessages(prev => [...prev, { type: 'bot', content: response.data.response }]);
      
      if (response.data.last_analysis) {
        setLastAnalysis(response.data.last_analysis);
      }
    } catch (error) {
      console.error('Error sending message:', error);
      setMessages(prev => [...prev, 
        { type: 'bot', content: 'Sorry, I encountered an error. Please try again.' }
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Container maxWidth="md" sx={{ height: '100vh', py: 4 }}>
        <Box sx={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
          <Box sx={{ 
            display: 'flex', 
            alignItems: 'center', 
            justifyContent: 'center',
            mb: 3,
            gap: 1
          }}>
            <Typography variant="h4" component="h1" sx={{ textAlign: 'center' }}>
              PropertyLoop - Real Estate Assistant
            </Typography>
          </Box>
          
          <Paper 
            elevation={0}
            sx={{ 
              flex: 1,
              mb: 3,
              p: 3,
              overflow: 'auto',
              bgcolor: '#FFFFFF',
              border: '1px solid rgba(30, 77, 140, 0.1)',
              height: '60vh',
              boxShadow: '0 0 15px rgba(30, 77, 140, 0.2)',
              '&:hover': {
                boxShadow: '0 0 20px rgba(30, 77, 140, 0.25)',
              },
            }}
          >
            {messages.map((message, index) => (
              <Box
                key={index}
                className="message-bubble"
                sx={{
                  display: 'flex',
                  justifyContent: message.type === 'user' ? 'flex-end' : 'flex-start',
                  mb: 2,
                }}
              >
                <Paper
                  elevation={0}
                  sx={{
                    p: 2,
                    maxWidth: '70%',
                    bgcolor: message.type === 'user' ? 'primary.main' : '#F8FAFD',
                    color: message.type === 'user' ? '#ffffff' : 'text.primary',
                    border: message.type === 'bot' ? '1px solid rgba(30, 77, 140, 0.1)' : 'none',
                    borderRadius: 3,
                    position: 'relative',
                    transition: 'all 0.2s ease',
                    '&:hover': {
                      transform: 'translateY(-1px)',
                      boxShadow: '0 4px 12px rgba(30, 77, 140, 0.1)',
                    },
                  }}
                >
                  {message.imageUrl && (
                    <Box sx={{ 
                      mb: 1, 
                      borderRadius: 2, 
                      overflow: 'hidden',
                      boxShadow: '0 2px 8px rgba(0, 0, 0, 0.1)'
                    }}>
                      <img 
                        src={message.imageUrl} 
                        alt="Uploaded" 
                        style={{ 
                          maxWidth: '100%',
                          display: 'block',
                          borderRadius: 8,
                        }} 
                      />
                    </Box>
                  )}
                  <Typography sx={{ whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>
                    {message.content}
                  </Typography>
                </Paper>
              </Box>
            ))}
            {loading && (
              <Box sx={{ display: 'flex', justifyContent: 'center', my: 2 }}>
                <CircularProgress size={24} sx={{ color: 'primary.main' }} />
              </Box>
            )}
            <div ref={messagesEndRef} />
          </Paper>

          <Box sx={{ mb: 2 }}>
            <Box
              {...getRootProps()}
              sx={{
                border: '2px dashed',
                borderColor: isDragActive ? 'primary.main' : 'rgba(30, 77, 140, 0.2)',
                borderRadius: 4,
                padding: 2,
                textAlign: 'center',
                cursor: 'pointer',
                bgcolor: isDragActive ? 'rgba(30, 77, 140, 0.04)' : '#FFFFFF',
                transition: 'all 0.2s ease',
                height: '100px',
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                justifyContent: 'center',
                '&:hover': {
                  borderColor: 'primary.main',
                  bgcolor: 'rgba(30, 77, 140, 0.02)',
                  boxShadow: '0 4px 12px rgba(30, 77, 140, 0.08)'
                }
              }}
            >
              <input {...getInputProps()} />
              <CloudUploadIcon sx={{ 
                fontSize: 36,
                color: theme.palette.primary.main,
                mb: 1,
                opacity: isDragActive ? 0.8 : 0.6,
              }} />
              <Typography sx={{ color: 'text.secondary', fontSize: '0.9rem' }}>
                {isDragActive ? 'Drop the image here...' : 'Drag and drop an image here, or click to select'}
              </Typography>
            </Box>
          </Box>

          <Grid container spacing={2}>
            <Grid item xs={12} md={3}>
              <TextField
                fullWidth
                label="Location (optional)"
                value={location}
                onChange={(e) => setLocation(e.target.value)}
                variant="outlined"
              />
            </Grid>
            <Grid item xs={12} md={7}>
              <TextField
                fullWidth
                label="Type your message"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyPress={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    handleSendMessage();
                  }
                }}
                multiline
                maxRows={3}
                variant="outlined"
              />
            </Grid>
            <Grid item xs={12} md={2}>
              <Button
                fullWidth
                variant="contained"
                color="primary"
                onClick={handleSendMessage}
                disabled={loading || !input.trim()}
                sx={{ 
                  height: '100%',
                  minHeight: 56,
                  background: 'linear-gradient(45deg, #1E4D8C 30%, #2E6BC4 90%)',
                  color: 'white !important',
                  '& .MuiButton-endIcon': {
                    color: 'white'
                  },
                  '&:hover': {
                    background: 'linear-gradient(45deg, #153761 30%, #1E4D8C 90%)',
                  },
                  '& .MuiSvgIcon-root': {
                    color: 'white'
                  }
                }}
                endIcon={<SendIcon />}
              >
                Send
              </Button>
            </Grid>
          </Grid>
        </Box>
      </Container>
    </ThemeProvider>
  );
};

export default App;