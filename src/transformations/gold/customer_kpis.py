from .country_summary import aggregate


def build(frame, timestamp, batch_id):
    result = aggregate(frame, [])
    result['gold_build_timestamp'] = timestamp
    result['source_batch_id'] = batch_id
    return result
