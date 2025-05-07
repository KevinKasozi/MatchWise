import { useState } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Grid,
  Tabs,
  Tab,
  Chip,
} from '@mui/material';
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '../api/client';
import type { Fixture, MatchResult } from '../types/api';

type FixtureStatus = 'upcoming' | 'completed' | 'all';

export default function Fixtures() {
  const [status, setStatus] = useState<FixtureStatus>('upcoming');

  const { data: fixtures, isLoading } = useQuery<(Fixture & { result?: MatchResult })[]>({
    queryKey: ['fixtures', status],
    queryFn: () =>
      apiClient
        .get('/fixtures', {
          params: { status },
        })
        .then((res) => res.data),
  });

  const handleStatusChange = (event: React.SyntheticEvent, newValue: FixtureStatus) => {
    setStatus(newValue);
  };

  if (isLoading) {
    return <Typography>Loading...</Typography>;
  }

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Football Fixtures
      </Typography>

      <Tabs
        value={status}
        onChange={handleStatusChange}
        sx={{ mb: 4 }}
      >
        <Tab label="Upcoming" value="upcoming" />
        <Tab label="Completed" value="completed" />
        <Tab label="All" value="all" />
      </Tabs>

      <Grid container spacing={3}>
        {fixtures?.map((fixture) => (
          <Grid item xs={12} key={fixture.id}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <Box>
                    <Typography variant="h6">
                      {fixture.home_team_id} vs {fixture.away_team_id}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      {new Date(fixture.match_date).toLocaleDateString()}
                    </Typography>
                  </Box>
                  <Box>
                    <Chip
                      label={fixture.stage}
                      color="primary"
                      size="small"
                      sx={{ mr: 1 }}
                    />
                    {fixture.result && (
                      <Typography variant="h6">
                        {fixture.result.home_score} - {fixture.result.away_score}
                      </Typography>
                    )}
                  </Box>
                </Box>
                {fixture.venue && (
                  <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                    Venue: {fixture.venue}
                  </Typography>
                )}
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>
    </Box>
  );
} 