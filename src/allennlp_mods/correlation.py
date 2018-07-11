''' Metric class for tracking correlations by saving predictions '''
import numpy as np
from overrides import overrides
from allennlp.training.metrics.metric import Metric
from sklearn.metrics import matthews_corrcoef
from scipy.stats import pearsonr, spearmanr
import torch

@Metric.register("correlation")
class Correlation(Metric):
    """Aggregate predictions, then calculate specified correlation"""
    def __init__(self, corr_type):
        self._predictions = []
        self._labels = []
        if corr_type == 'pearson':
            corr_fn = pearsonr
        elif corr_type == 'spearman':
            corr_fn = spearmanr
        elif corr_type == 'matthews':
            corr_fn = matthews_corrcoef
        else:
            raise ValueError("Correlation type not supported")
        self._corr_fn = corr_fn
        self.corr_type = corr_type

        self._history = [] # for debugging purposes more than anything else
        self._per_batch_history = []

    def _correlation(self, labels, predictions):
        corr = self._corr_fn(labels, predictions)
        if self.corr_type in ['pearson', 'spearman']:
            corr = corr[0]
        return corr

    def __call__(self, predictions, labels):
        """ Accumulate statistics for a set of predictions and labels.

        Args:
            predictions: Tensor or np.array of shape
            labels: Tensor or np.array of same shape as predictions
        """
        # Convert from Tensor if necessary
        if isinstance(predictions, torch.Tensor):
            predictions = predictions.cpu().numpy()
        if isinstance(labels, torch.Tensor):
            labels = labels.cpu().numpy()

        # Verify shape match
        assert predictions.shape == labels.shape, ("Predictions and labels must"
                                                   " have matching shape. Got:"
                                                   " preds=%s, labels=%s" % (
                                                       str(predictions.shape),
                                                       str(labels.shape)))
        predictions = list(predictions.flatten())
        labels = list(labels.flatten())

        if hasattr(self, '_per_batch_history'):
            batch_corr = self._correlation(labels, predictions)
            self._per_batch_history.append(batch_corr)

        self._predictions += predictions
        self._labels += labels

        if hasattr(self, '_history'):
            corr = self._correlation(self._labels, self._predictions)
            self._history.append(corr)

    def get_metric(self, reset=False):
        correlation = self._correlation(self._labels, self._predictions)
        if reset:
            self.reset()
        return correlation

    @overrides
    def reset(self):
        self._predictions = []
        self._labels = []
        self._history = []
        self._per_batch_history = []
