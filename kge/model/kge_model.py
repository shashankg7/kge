import torch


class KgeBase(torch.nn.Module):
    """
    Base class for all relational models and embedders
    """

    def __init__(self, config, dataset):
        super().__init__()
        self.config = config
        self.dataset = dataset

    def initialize(self, what, initialize, initialize_arg):
        if initialize == 'normal':
            torch.nn.init.normal_(what, std=initialize_arg)
        else:
            raise ValueError("initialize")


class KgeModel(KgeBase):
    """
    Base class for all relational models
    """

    def __init__(self, config, dataset):
        super().__init__(config, dataset)

    def score_spo(self, s, p, o, is_training=False):
        return self._score(s, p, o, is_training=is_training)

    def score_sp(self, s, p, is_training=False):
        s = self.entity_embedder.embed(s, is_training)
        p = self.relation_embedder.embed(rel)
        all_objects = self.entity_embedder.embed_all(is_training)
        return self._score(s, p, all_objects, prefix='sp', is_training=is_training)

    def score_po(self, p, o, is_training=False):
        all_subjects = self.entity_embedder.embed_all(is_training)
        p = self.relation_embedder.embed(p, is_training)
        o = self.entity_embedder.embed(o, is_training)
        return self._score(all_subjects, p, o, prefix='po', is_training=is_training)

    def score_sp_po(self, s, p, o, is_training=False):
        s = self.entity_embedder.embed(s, is_training)
        p = self.relation_embedder.embed(p, is_training)
        o = self.entity_embedder.embed(o, is_training)
        all_entities = self.entity_embedder.embed_all(is_training)
        sp_scores = self._score(s, p, all_entities, prefix='sp', is_training=is_training)
        po_scores = self._score(all_entities, p, o, prefix='po', is_training=is_training)
        return torch.cat((sp_scores, po_scores), dim=1)

    def score_p(self, p, is_training=False):
        raise NotImplementedError

    def create(config, dataset):
        """Factory method for model creation."""
        from kge.model import ComplEx

        ## create the embedders
        model = None
        if config.get('model.type') == 'complex':
            model = ComplEx(config, dataset)
        else:
            # perhaps TODO: try class with specified name -> extensibility
            raise ValueError('model.type')

        # TODO I/O (resume model)
        model.to(config.get('job.device'))
        return model


    # TODO document this method and in particular: prefix
    def _score(self, s, p, o, prefix=None, is_training=False):
        r"""
        :param s: tensor of size [batch_size, embedding_size]
        :param p: tensor of size [batch_size, embedding_size]
        :param o:: tensor of size [batch_size, embedding_size]
        :return: score tensor of size [batch_size, 1]"""


class KgeEmbedder(KgeBase):
    """
    Base class for all relational model embedders
    """

    def __init__(self, config, dataset, is_entity_embedder):
        super().__init__(config, dataset)
        self.is_entity_embedder = is_entity_embedder

    def create(config, dataset, is_entity_embedder):
        """Factory method for embedder creation."""
        from kge.model import LookupEmbedder

        embedder_type = KgeEmbedder._get_option(config, 'model.embedder', is_entity_embedder)
        if embedder_type == 'lookup':
            return LookupEmbedder(config, dataset, is_entity_embedder)
        else:
            raise ValueError('embedder')

    def embed(self, indexes, is_training=False) -> torch.Tensor:
        """
        Computes the embedding.
        """
        raise NotImplementedError

    def embed_all(self, is_training=False) -> torch.Tensor:
        """
        Returns all embeddings.
        """
        raise NotImplementedError

        # TODO I/O

    def get_option(self, name):
        return KgeEmbedder._get_option(self.config, name, self.is_entity_embedder)

    def _get_option(config, name, is_entity_embedder):
        value = config.get(name)
        if type(value) == list:
            return value[0 if self.is_entity_embedder else 1]
        else:
            return value