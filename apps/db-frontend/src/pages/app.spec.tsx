import { render } from '@testing-library/react';

import App from '../App';

describe('App', () => {
  it('should render successfully', () => {
    const { baseElement } = render(<App />);
    expect(baseElement).toBeTruthy();
  });

  it('should have a greeting as the title', () => {
    const { getAllByText } = render(<App />);
    expect(getAllByText(new RegExp('Welcome db-frontend', 'gi')).length > 0).toBeTruthy();
  });
});
