from transformers import Wav2Vec2CTCTokenizer, Wav2Vec2FeatureExtractor, Wav2Vec2Processor

tokenizer = Wav2Vec2CTCTokenizer(
    "urdu_phoneme_vocab.json",
    unk_token="[UNK]", pad_token="[PAD]", word_delimiter_token="|",
)
feature_extractor = Wav2Vec2FeatureExtractor.from_pretrained("facebook/wav2vec2-xls-r-300m")
processor = Wav2Vec2Processor(feature_extractor=feature_extractor, tokenizer=tokenizer)
processor.save_pretrained("./urdu-phoneme-processor")