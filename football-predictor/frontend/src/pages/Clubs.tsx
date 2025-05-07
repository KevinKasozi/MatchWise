import { useState } from 'react';
import {
  Box,
  Typography,
  TextField,
  Card,
  CardContent,
  Grid,
  Pagination,
} from '@mui/material';
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '../api/client';
import type { Club } from '../types/api';

export default function Clubs() {
  const [search, setSearch] = useState('');
  const [page, setPage] = useState(1);
  const itemsPerPage = 12;

  const { data: clubs, isLoading } = useQuery<Club[]>({
    queryKey: ['clubs', search, page],
    queryFn: () =>
      apiClient
        .get('/clubs', {
          params: {
            search,
            skip: (page - 1) * itemsPerPage,
            limit: itemsPerPage,
          },
        })
        .then((res) => res.data),
  });

  const handleSearchChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setSearch(event.target.value);
    setPage(1);
  };

  const handlePageChange = (event: React.ChangeEvent<unknown>, value: number) => {
    setPage(value);
  };

  if (isLoading) {
    return <Typography>Loading...</Typography>;
  }

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Football Clubs
      </Typography>

      <TextField
        fullWidth
        label="Search clubs"
        variant="outlined"
        value={search}
        onChange={handleSearchChange}
        sx={{ mb: 4 }}
      />

      <Grid container spacing={3}>
        {clubs?.map((club) => (
          <Grid item xs={12} sm={6} md={4} lg={3} key={club.id}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  {club.name}
                </Typography>
                {club.country && (
                  <Typography variant="body2" color="text.secondary">
                    Country: {club.country}
                  </Typography>
                )}
                {club.founded_year && (
                  <Typography variant="body2" color="text.secondary">
                    Founded: {club.founded_year}
                  </Typography>
                )}
                {club.stadium_name && (
                  <Typography variant="body2" color="text.secondary">
                    Stadium: {club.stadium_name}
                  </Typography>
                )}
                {club.city && (
                  <Typography variant="body2" color="text.secondary">
                    City: {club.city}
                  </Typography>
                )}
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      <Box sx={{ mt: 4, display: 'flex', justifyContent: 'center' }}>
        <Pagination
          count={Math.ceil((clubs?.length || 0) / itemsPerPage)}
          page={page}
          onChange={handlePageChange}
          color="primary"
        />
      </Box>
    </Box>
  );
} 