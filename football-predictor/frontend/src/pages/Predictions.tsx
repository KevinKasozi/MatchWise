import { useState } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Grid,
  LinearProgress,
  Button,
} from '@mui/material';
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '../api/client';
import type { Fixture, Prediction } from '../types/api';

export default function Predictions() {
  const [selectedFixture, setSelectedFixture] = useState<number | null>(null);

  const { data: fixtures, isLoading: fixturesLoading } = useQuery<Fixture[]>({
    queryKey: ['upcomingFixtures'],
    queryFn: () =>
      apiClient
        .get('/fixtures', {
          params: { status: 'upcoming' },
        })
        .then((res) => res.data),
  });

  const { data: prediction, isLoading: predictionLoading } = useQuery<Prediction>({
    queryKey: ['prediction', selectedFixture],
    queryFn: () =>
      apiClient
        .get(`/predictions/${selectedFixture}`)
        .then((res) => res.data),
    enabled: !!selectedFixture,
  });

  const handlePredict = (fixtureId: number) => {
    setSelectedFixture(fixtureId);
  };

  if (fixturesLoading) {
    return <Typography>Loading fixtures...</Typography>;
  }

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Match Predictions
      </Typography>

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
                  <Button
                    variant="contained"
                    onClick={() => handlePredict(fixture.id)}
                    disabled={predictionLoading && selectedFixture === fixture.id}
                  >
                    Predict
                  </Button>
                </Box>

                {selectedFixture === fixture.id && prediction && (
                  <Box sx={{ mt: 2 }}>
                    <Typography variant="subtitle1" gutterBottom>
                      Prediction Results
                    </Typography>
                    <Grid container spacing={2}>
                      <Grid item xs={12}>
                        <Typography variant="body2">Home Win</Typography>
                        <LinearProgress
                          variant="determinate"
                          value={prediction.home_win_probability * 100}
                          sx={{ height: 10, borderRadius: 5 }}
                        />
                        <Typography variant="body2" color="text.secondary">
                          {(prediction.home_win_probability * 100).toFixed(1)}%
                        </Typography>
                      </Grid>
                      <Grid item xs={12}>
                        <Typography variant="body2">Draw</Typography>
                        <LinearProgress
                          variant="determinate"
                          value={prediction.draw_probability * 100}
                          sx={{ height: 10, borderRadius: 5 }}
                        />
                        <Typography variant="body2" color="text.secondary">
                          {(prediction.draw_probability * 100).toFixed(1)}%
                        </Typography>
                      </Grid>
                      <Grid item xs={12}>
                        <Typography variant="body2">Away Win</Typography>
                        <LinearProgress
                          variant="determinate"
                          value={prediction.away_win_probability * 100}
                          sx={{ height: 10, borderRadius: 5 }}
                        />
                        <Typography variant="body2" color="text.secondary">
                          {(prediction.away_win_probability * 100).toFixed(1)}%
                        </Typography>
                      </Grid>
                      {prediction.predicted_home_score !== undefined && (
                        <Grid item xs={12}>
                          <Typography variant="subtitle1">
                            Predicted Score: {prediction.predicted_home_score} - {prediction.predicted_away_score}
                          </Typography>
                        </Grid>
                      )}
                    </Grid>
                  </Box>
                )}
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>
    </Box>
  );
} 