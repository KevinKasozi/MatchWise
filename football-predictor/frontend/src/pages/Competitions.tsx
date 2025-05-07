import { useState } from 'react';
import {
  Box,
  Typography,
  Tabs,
  Tab,
  Card,
  CardContent,
  Grid,
} from '@mui/material';
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '../api/client';
import type { Competition } from '../types/api';

type CompetitionType = 'league' | 'cup' | 'international';

export default function Competitions() {
  const [selectedType, setSelectedType] = useState<CompetitionType>('league');

  const { data: competitions, isLoading } = useQuery<Competition[]>({
    queryKey: ['competitions', selectedType],
    queryFn: () =>
      apiClient
        .get('/competitions', {
          params: { competition_type: selectedType },
        })
        .then((res) => res.data),
  });

  const handleTypeChange = (event: React.SyntheticEvent, newValue: CompetitionType) => {
    setSelectedType(newValue);
  };

  if (isLoading) {
    return <Typography>Loading...</Typography>;
  }

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Football Competitions
      </Typography>

      <Tabs
        value={selectedType}
        onChange={handleTypeChange}
        sx={{ mb: 4 }}
      >
        <Tab label="Leagues" value="league" />
        <Tab label="Cups" value="cup" />
        <Tab label="International" value="international" />
      </Tabs>

      <Grid container spacing={3}>
        {competitions?.map((competition) => (
          <Grid item xs={12} sm={6} md={4} key={competition.id}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  {competition.name}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Country: {competition.country}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Type: {competition.competition_type}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>
    </Box>
  );
} 