import React, { useState, useEffect } from "react";
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Grid,
  TextField,
  IconButton,
} from "@mui/material";
import CloseIcon from "@mui/icons-material/Close";
import api from "../services/api";

const ImageDialog = ({ open, onClose, token }) => {
  const [thumbnails, setThumbnails] = useState([]);
  const [selectedImage, setSelectedImage] = useState(null);
  const [markdownText, setMarkdownText] = useState("");
  const [codeText, setCodeText] = useState("");

  useEffect(() => {
    if (open) {
      fetchThumbnails();
    }
  }, [open]);

  const fetchThumbnails = async () => {
    try {
      //const response = await fetch("/api/thumbnails");
      const response = await api.get("/thumbnails", {
        headers: { Authorization: `Bearer ${token}` },
      });
      const data = await response.json();
      setThumbnails(data);
    } catch (error) {
      console.error("Error fetching thumbnails:", error);
    }
  };

  const handleImageSelect = async (filename) => {
    try {
      const response = await fetch(`/api/image/${filename}`);
      const data = await response.json();
      setSelectedImage(data.image);
      setMarkdownText(data.markdownText);
      setCodeText(data.codeText);
    } catch (error) {
      console.error("Error fetching image details:", error);
    }
  };

  const handleApiCall = async (endpoint) => {
    try {
      await fetch(`/api/${endpoint}`);
      // Handle the response as needed
    } catch (error) {
      console.error(`Error calling ${endpoint} API:`, error);
    }
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="lg" fullWidth>
      <DialogTitle>
        Image Viewer
        <IconButton
          aria-label="close"
          onClick={onClose}
          sx={{ position: "absolute", right: 8, top: 8 }}
        >
          <CloseIcon />
        </IconButton>
      </DialogTitle>
      <DialogContent>
        <Grid container spacing={2}>
          <Grid item xs={3}>
            {thumbnails.map((thumb) => (
              <img
                key={thumb.filename}
                src={`data:image/jpeg;base64,${thumb.thumbnail}`}
                alt={thumb.filename}
                style={{
                  width: "100%",
                  marginBottom: "10px",
                  cursor: "pointer",
                }}
                onClick={() => handleImageSelect(thumb.filename)}
              />
            ))}
          </Grid>
          <Grid item xs={9}>
            {selectedImage && (
              <img
                src={selectedImage}
                alt="Selected"
                style={{ width: "100%" }}
              />
            )}
            <TextField
              label="Markdown Text"
              multiline
              rows={4}
              value={markdownText}
              fullWidth
              variant="outlined"
              margin="normal"
              InputProps={{ readOnly: true }}
            />
            <TextField
              label="Code Text"
              multiline
              rows={4}
              value={codeText}
              fullWidth
              variant="outlined"
              margin="normal"
              InputProps={{ readOnly: true }}
            />
          </Grid>
        </Grid>
      </DialogContent>
      <DialogActions>
        <Button onClick={() => handleApiCall("reseeandwrite")}>
          再看和写1次
        </Button>
        <Button onClick={() => handleApiCall("rewrite")}>再写1次</Button>
        <Button onClick={() => handleApiCall("copycode")}>复制程式码</Button>
        <Button onClick={onClose}>关闭</Button>
      </DialogActions>
    </Dialog>
  );
};

export default ImageDialog;
