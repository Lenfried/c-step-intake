/**
 * Staff-only summary of an application's latest eligibility decision.
 *
 * Reads GET @eligibility. The service answers every viewer without an error
 * and only includes the decision for users with the review permission, so
 * applicants and drafts simply render nothing.
 */
import React, { useEffect, useState } from 'react';
import { useDispatch } from 'react-redux';
import { Label, Message, Segment, Table } from 'semantic-ui-react';
import { overallColor, statusColor } from './eligibilityDisplay';

const GET_ELIGIBILITY = 'C_STEP_INTAKE_GET_ELIGIBILITY';

const EligibilityPanel = ({ path, reviewState, schema }) => {
  const dispatch = useDispatch();
  const [data, setData] = useState(null);

  useEffect(() => {
    let cancelled = false;
    // Volto's api middleware handles any action with a `request` and
    // returns the response body; no reducer is needed for a one-off read.
    dispatch({
      type: GET_ELIGIBILITY,
      request: { op: 'get', path: `${path}/@eligibility` },
    })
      .then((result) => !cancelled && setData(result))
      .catch(() => !cancelled && setData(null));
    return () => {
      cancelled = true;
    };
    // Re-read after a workflow change: a resubmission adds a decision.
  }, [dispatch, path, reviewState]);

  const latest = data?.available ? data.latest : null;
  if (!latest) {
    return null;
  }
  const eligibility = latest.eligibility;
  const titleOf = (name) => schema?.properties?.[name]?.title || name;

  return (
    <Segment className="c-step-intake-eligibility" color="blue">
      <h2 style={{ fontSize: '1.15em', marginTop: 0 }}>Eligibility check</h2>
      <p>
        Automatic check of the answers against the acceptance criteria. Visible
        to program staff only. Staff make the decision.
      </p>

      {eligibility ? (
        <>
          <p>
            <Label color={overallColor(eligibility.overall)} size="large">
              {eligibility.overall}
            </Label>
          </p>
          <Table compact celled unstackable>
            <Table.Body>
              {eligibility.checks.map((check) => (
                <Table.Row key={check.condition}>
                  <Table.Cell collapsing>{check.condition}</Table.Cell>
                  <Table.Cell collapsing>
                    <Label color={statusColor(check.status)}>
                      {check.status}
                    </Label>
                  </Table.Cell>
                  <Table.Cell>{check.detail}</Table.Cell>
                </Table.Row>
              ))}
            </Table.Body>
          </Table>
        </>
      ) : (
        <p>{latest.reason}</p>
      )}

      {latest.missing_fields.length > 0 && (
        <Message warning>
          Missing required answers:{' '}
          {latest.missing_fields.map(titleOf).join(', ')}
        </Message>
      )}

      <p style={{ color: '#767676', fontSize: '0.9em', marginTop: '1em' }}>
        Checked {new Date(latest.decided_at).toLocaleString()} · rules{' '}
        {latest.rules_version}
        {data.decisions > 1 && ` · ${data.decisions} submissions`}
      </p>
    </Segment>
  );
};

export default EligibilityPanel;
