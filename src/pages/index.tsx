import React, { useState, useEffect, useRef } from "react";
import {
  Typography,
  TextField,
  Button,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  Container,
  Box,
  IconButton,
  Tooltip,
} from "@mui/material";
import AddIcon from "@mui/icons-material/Add";
import { useAuth } from "../hooks/useAuth";
import { useRouter } from "next/router";

interface Element {
  name: string;
  xpath: string;
  url: string;
}

interface ScrapeResult {
  xpath: string;
  text: string;
  name: string;
}

type Result = {
  [key: string]: ScrapeResult[];
};

function validateURL(url: string): boolean {
  try {
    new URL(url);
    return true;
  } catch (_) {
    return false;
  }
}

const Home = () => {
  const { user } = useAuth();
  const router = useRouter();

  const { elements, url } = router.query;

  const [submittedURL, setSubmittedURL] = useState("");
  const [isValidURL, setIsValidUrl] = useState<boolean>(true);
  const [urlError, setUrlError] = useState<string | null>(null);
  const [rows, setRows] = useState<Element[]>([]);
  const [results, setResults] = useState<null | Result>(null);
  const [newRow, setNewRow] = useState<Element>({
    name: "",
    xpath: "",
    url: "",
  });

  const resultsRef = useRef<HTMLTableElement | null>(null);

  useEffect(() => {
    if (elements) {
      setRows(JSON.parse(elements as string));
    }
    if (url) {
      setSubmittedURL(url as string);
    }
  }, [elements, url]);

  useEffect(() => {
    if (results && resultsRef.current) {
      resultsRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [results]);

  const handleAddRow = () => {
    const updatedRow = { ...newRow, url: submittedURL };
    setRows([...rows, updatedRow]);
    setNewRow({ name: "", xpath: "", url: "" });
  };

  const handleDeleteRow = (elementName: string) => {
    setRows(
      rows.filter((r) => {
        return elementName !== r.name;
      }),
    );
  };

  const handleSubmit = () => {
    if (!validateURL(submittedURL)) {
      setIsValidUrl(false);
      setUrlError("Please enter a valid URL.");
      return;
    }

    setIsValidUrl(true);
    setUrlError(null);

    fetch("/api/submit-scrape-job", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({
        url: submittedURL,
        elements: rows,
        user: user?.email,
        time_created: new Date().toISOString(),
      }),
    })
      .then((response) => response.json())
      .then((data) => setResults(data));
  };

  return (
    <Box
      display="flex"
      flexDirection="column"
      justifyContent="center"
      alignItems="center"
      minHeight="100vh"
      py={4}
    >
      <Container maxWidth="md">
        <Typography variant="h1" gutterBottom textAlign="center">
          Web Scraper
        </Typography>
        <div
          style={{ marginBottom: "20px" }}
          className="flex flex-row space-x-4 items-center"
        >
          <TextField
            label="URL"
            variant="outlined"
            fullWidth
            value={submittedURL}
            onChange={(e) => setSubmittedURL(e.target.value)}
            error={!isValidURL}
            helperText={!isValidURL ? urlError : ""}
          />
          <Button
            className="!text-black"
            variant="contained"
            color="primary"
            size="small"
            onClick={handleSubmit}
            disabled={!(rows.length > 0)}
          >
            Submit
          </Button>
        </div>
        <Box display="flex" gap={2} marginBottom={2} className="items-center">
          <TextField
            label="Name"
            variant="outlined"
            fullWidth
            value={newRow.name}
            onChange={(e) => setNewRow({ ...newRow, name: e.target.value })}
          />
          <TextField
            label="XPath"
            variant="outlined"
            fullWidth
            value={newRow.xpath}
            onChange={(e) => setNewRow({ ...newRow, xpath: e.target.value })}
          />
          <Tooltip
            title={
              newRow.xpath.length > 0 && newRow.name.length > 0
                ? "Add Element"
                : "Fill out all fields to add an element"
            }
            placement="top"
          >
            <span>
              <IconButton
                aria-label="add"
                size="small"
                onClick={handleAddRow}
                sx={{ height: "40px", width: "40px" }}
                disabled={!(newRow.xpath.length > 0 && newRow.name.length > 0)}
              >
                <AddIcon fontSize="inherit" sx={{ color: "black" }} />
              </IconButton>
            </span>
          </Tooltip>
        </Box>
        <Typography variant="h4">Elements</Typography>
        <Table className="mb-4">
          <TableHead>
            <TableRow>
              <TableCell>Name</TableCell>
              <TableCell>XPath</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {rows.map((row, index) => (
              <TableRow key={index}>
                <TableCell>
                  <TextField variant="outlined" fullWidth value={row.name} />
                </TableCell>
                <TableCell>
                  <TextField variant="outlined" fullWidth value={row.xpath} />
                </TableCell>
                <TableCell>
                  <Button onClick={() => handleDeleteRow(row.name)}>
                    Delete
                  </Button>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
        {results && (
          <>
            <Typography variant="h4">Results</Typography>
            <Table ref={resultsRef} style={{ marginTop: "20px" }}>
              <TableHead>
                <TableRow>
                  <TableCell>Name</TableCell>
                  <TableCell>XPath</TableCell>
                  <TableCell>Text</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {Object.keys(results).map((key, index) => (
                  <React.Fragment key={index}>
                    {results[key].map((result, resultIndex) => (
                      <TableRow key={resultIndex}>
                        <TableCell>{result.name}</TableCell>
                        <TableCell>{result.xpath}</TableCell>
                        <TableCell>{result.text}</TableCell>
                      </TableRow>
                    ))}
                  </React.Fragment>
                ))}
              </TableBody>
            </Table>
          </>
        )}
      </Container>
    </Box>
  );
};

export default Home;
