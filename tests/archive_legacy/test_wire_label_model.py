from talustrace.backend.models import Wire, WireLabel


def test_wire_label_model_roundtrip():
    w = Wire(id='W1', **{'from': 'D1.1', 'to': 'D2.1'})
    w.labels.append(WireLabel(text='PWR', t_pos=0.33))
    d = w.model_dump()
    assert 'labels' in d
    # round-trip
    # Use the Pydantic v2 compatible API
    w2 = Wire.model_validate(d)
    assert len(w2.labels) == 1
    assert w2.labels[0].text == 'PWR'
    assert abs(w2.labels[0].t_pos - 0.33) < 1e-6
